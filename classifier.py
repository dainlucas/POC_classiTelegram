import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from typesafe_sdk import AsyncTypeSafeClient, Choice

logger = logging.getLogger(__name__)


class JevClassifier:
    """Classificador de mensagens em categorias personalizadas utilizando o JEV AI (TypeSafe AI)."""

    DEFAULT_INSTRUCTIONS = (
        "Classifique a mensagem recebida na categoria mais adequada entre as opções fornecidas. "
        "Se a mensagem não se encaixar com clareza em nenhuma categoria de produto/hardware específica, "
        "classifique-a como 'OUTROS'."
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        categories_path: str | Path = "categories.json",
        instructions: Optional[str] = None,
        simulate: bool = False,
    ):
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY")
        self.categories_path = Path(categories_path)
        self.instructions = instructions or self.DEFAULT_INSTRUCTIONS
        self.simulate = simulate
        self.categories = self._load_categories()

        self._client: Optional[AsyncTypeSafeClient] = None
        if not self.simulate and self.api_key:
            self._client = AsyncTypeSafeClient(api_key=self.api_key)
        elif not self.simulate and not self.api_key:
            logger.warning(
                "Nenhuma TYPESAFE_API_KEY foi informada. Ativando modo de simulação/mock."
            )
            self.simulate = True

    def _load_categories(self) -> Dict[str, str]:
        """Carrega o dicionário de categorias a partir do arquivo JSON."""
        if not self.categories_path.exists():
            logger.warning(
                f"Arquivo de categorias {self.categories_path} não encontrado. Usando categorias padrão."
            )
            return {
                "PROCESSADOR_NVIDIA": "Processadores ou CPUs Nvidia",
                "PLACA_DE_VIDEO_AMD": "Placas de vídeo AMD Radeon",
                "NVIDIA_SERIE_3000": "Placas de vídeo Nvidia GeForce RTX série 3000",
                "OUTROS": "Outros assuntos ou categorias não correspondentes",
            }

        with open(self.categories_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Categorias carregadas ({len(data)}): {list(data.keys())}")
            return data

    def reload_categories(self) -> Dict[str, str]:
        """Recarrega as categorias do arquivo JSON para refletir alterações em tempo de execução."""
        self.categories = self._load_categories()
        return self.categories

    def set_categories(self, categories: Dict[str, str]) -> None:
        """Atualiza dinamicamente o mapa de categorias."""
        self.categories = categories
        logger.info(f"Categorias atualizadas: {list(self.categories.keys())}")

    async def classify(self, text: str) -> Dict[str, Any]:
        """Classifica uma mensagem de texto usando o JEV AI (System One).

        Retorna:
            dict com:
                - category: Nome da categoria escolhida
                - confidence: Grau de confiança (0.0 a 1.0)
                - probabilities: Probabilidade atribuída a cada categoria
                - is_simulation: Booleano indicando se foi resultado de simulação
        """
        clean_text = (text or "").strip()
        if not clean_text:
            return {
                "category": "OUTROS",
                "confidence": 1.0,
                "probabilities": {"OUTROS": 1.0},
                "is_simulation": self.simulate,
            }

        # Modo de simulação para desenvolvimento local e testes offline
        if self.simulate or not self._client:
            return self._simulate_classification(clean_text)

        try:
            # Monta a pergunta Choice para o JEV AI com as categorias configuradas
            choice_question = Choice(
                instructions=self.instructions,
                criteria=self.categories,
            )

            response = await self._client.system_one(
                state=clean_text,
                questions={"categoria": choice_question},
            )

            answer = response.choices["categoria"]
            return {
                "category": answer.choice,
                "confidence": round(answer.confidence, 4),
                "probabilities": {
                    k: round(v, 4) for k, v in answer.probabilities.items()
                },
                "is_simulation": False,
            }
        except Exception as e:
            logger.error(f"Erro ao consultar JEV AI: {e}", exc_info=True)
            raise

    def _simulate_classification(self, text: str) -> Dict[str, Any]:
        """Classificação heurística local para simular respostas do JEV AI durante testes."""
        upper = text.upper()
        # Verificação simples de palavras-chave para teste
        if any(w in upper for w in ["3060", "3070", "3080", "3090", "RTX 30", "SÉRIE 3000", "SERIE 3000"]):
            selected = "NVIDIA_SERIE_3000"
        elif any(w in upper for w in ["AMD", "RADEON", "RX 6600", "RX 6700", "RX 7800", "RX 580"]):
            selected = "PLACA_DE_VIDEO_AMD"
        elif any(w in upper for w in ["TEGRA", "GRACE", "CPU NVIDIA", "PROCESSADOR NVIDIA"]):
            selected = "PROCESSADOR_NVIDIA"
        else:
            selected = "OUTROS" if "OUTROS" in self.categories else list(self.categories.keys())[0]

        probs = {cat: 0.05 for cat in self.categories}
        probs[selected] = 0.85

        return {
            "category": selected,
            "confidence": 0.85,
            "probabilities": probs,
            "is_simulation": True,
        }

    async def close(self) -> None:
        """Fecha conexões ativas do cliente TypeSafe."""
        if self._client:
            await self._client.aclose()
            self._client = None

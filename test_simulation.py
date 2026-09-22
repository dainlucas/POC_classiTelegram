#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from classifier import JevClassifier

load_dotenv()


SAMPLE_MESSAGES = [
    {
        "grupo": "Grupo Bazar Hardware BR",
        "usuario": "gamer_sp",
        "texto": "Vendo GeForce RTX 3080 10GB Rog Strix impecável, acompanha caixa e nota. R$ 2.700,00",
        "esperado": "NVIDIA_SERIE_3000",
    },
    {
        "grupo": "Promoções e Descontos PC",
        "usuario": "ofertas_bot",
        "texto": "🔥 OPORTUNIDADE: Placa de Vídeo AMD Radeon RX 6700 XT 12GB Speedster por R$ 2.199 em até 10x!",
        "esperado": "PLACA_DE_VIDEO_AMD",
    },
    {
        "grupo": "Tech & Datacenter News",
        "usuario": "dev_cloud",
        "texto": "A Nvidia anunciou novos processadores Grace Hopper com 72 núcleos Arm Neoverse focados em IA e HPC.",
        "esperado": "PROCESSADOR_NVIDIA",
    },
    {
        "grupo": "Grupo Hardware e Trocas",
        "usuario": "marcelo_rs",
        "texto": "Boa tarde pessoal, uma fonte de 650W aguenta bem essa configuração ou preciso de uma de 750W?",
        "esperado": "OUTROS",
    },
    {
        "grupo": "Vendas TI & Peças",
        "usuario": "pedro_ti",
        "texto": "Disponível: RTX 3060 12GB Galax com 6 meses de garantia restante. Entrego em mãos em SP.",
        "esperado": "NVIDIA_SERIE_3000",
    },
]


async def run_samples(classifier: JevClassifier) -> None:
    print("\n" + "=" * 75)
    print("🚀 TESTE DE CLASSIFICAÇÃO COM JEV AI")
    print("=" * 75)
    print(f"📋 Categorias ativas ({len(classifier.categories)}):")
    for cat, desc in classifier.categories.items():
        print(f"  • {cat}: {desc}")
    print("-" * 75)

    mode_str = "Simulação Local (sem API key)" if classifier.simulate else "API Oficial JEV AI (TypeSafe)"
    print(f"⚙️  Modo de execução: {mode_str}\n")

    for i, msg in enumerate(SAMPLE_MESSAGES, start=1):
        print(f"[{i}/{len(SAMPLE_MESSAGES)}] Mensagem recebida no grupo '{msg['grupo']}' (de @{msg['usuario']}):")
        print(f"  💬 \"{msg['texto']}\"")

        res = await classifier.classify(msg["texto"])
        cat = res["category"]
        conf = res["confidence"] * 100

        icon = "✅" if cat == msg["esperado"] else "⚠️"
        print(f"  {icon} Categoria: {cat} (Confiança: {conf:.1f}%) [Esperado: {msg['esperado']}]")
        print("-" * 75)


async def run_interactive(classifier: JevClassifier) -> None:
    print("\n✍️  MODO INTERATIVO: Digite qualquer mensagem para classificar (ou 'sair' para encerrar):")
    while True:
        try:
            line = input("\nDigite a mensagem: ").strip()
            if not line or line.lower() in {"sair", "exit", "quit"}:
                print("Encerrando modo interativo.")
                break

            res = await classifier.classify(line)
            print(f"🏷️  Categoria: {res['category']} (Confiança: {res['confidence']*100:.1f}%)")
            print("📊 Probabilidades detalhadas:")
            for c, prob in sorted(res.get("probabilities", {}).items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(prob * 20)
                print(f"   - {c:20s}: {prob*100:5.1f}% | {bar}")
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando.")
            break


async def main():
    api_key = os.getenv("TYPESAFE_API_KEY")
    use_simulation = "--simulate" in sys.argv or not api_key

    classifier = JevClassifier(api_key=api_key, simulate=use_simulation)
    try:
        await run_samples(classifier)
        if "--interactive" in sys.argv or "-i" in sys.argv:
            await run_interactive(classifier)
    finally:
        await classifier.close()


if __name__ == "__main__":
    asyncio.run(main())

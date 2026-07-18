"""Pipeline reproduzível de fine-tuning: gera dataset, treina e avalia.

Uso: python run_all.py
"""

import generate_dataset
import finetune
import evaluate


def main():
    print("== 1. Gerando dataset ==")
    generate_dataset.gerar()
    print("== 2. Fine-tuning ==")
    finetune.finetunar()
    print("== 3. Avaliando e gerando relatório ==")
    evaluate.main()


if __name__ == "__main__":
    main()

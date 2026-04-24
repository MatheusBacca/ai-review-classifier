from transformers import pipeline
from app.config import settings

classifier = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    token=settings.huggingface_token,
)


def classificar_reviews(lista_reviews):
    resultados = []

    for item in lista_reviews:
        texto = item["review"]

        # Classificação usando o modelo
        resultado = classifier(texto)[0]

        resultados.append(
            {
                "nome": item["nome"],
                "data": item["data"],
                "review": texto,
                "classificacao": resultado["label"],
                "score": round(resultado["score"], 4),
            }
        )

    return resultados


if __name__ == "__main__":
    reviews = [
        {
            "nome": "João",
            "data": "2026-04-20",
            "review": "Produto excelente, chegou rápido e bem embalado!",
        },
        {
            "nome": "Maria",
            "data": "2026-04-21",
            "review": "Demorou muito e veio com defeito.",
        },
        {
            "nome": "Carlos",
            "data": "2026-04-22",
            "review": "Ok, nada demais. Cumpre o que promete.",
        },
    ]

    saida = classificar_reviews(reviews)

    for r in saida:
        print(
            f"""
Nome: {r['nome']}
Data: {r['data']}
Review: {r['review']}
Classificação: {r['classificacao']}
Confiança: {r['score']}
-----------------------------
"""
        )

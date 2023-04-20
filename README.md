# gpt-proxy-poc

A proxy between [UI](https://github.com/kevinikos/gpt-poc-ui) and Weaviate instance populated by [backend](https://github.com/damiankryger/gpt-poc).

## How to run

1. Prepare virtual environment.

```shell
python -m venv venv
```

2. Install dependencies.

```shell
pip install -r requirements.txt
```

3. Run server.

```shell
uvicorn main:app --reload 
```

## How to use

```shell
curl --location 'http://localhost:8000/summary' \
-H 'Content-Type: application/json' \
-d '{
    "countries": [
        "Syria",
        "Italy"
    ]
}'
```

and the response should be like

```json
[
    {
        "country": "Syria",
        "summary": "Syria's ongoing war has led to significant economic problems, including high inflation, declining industrial production, and limited foreign trade. The conflict has destroyed infrastructure, led to job losses, and caused high living costs. The region's humanitarian crisis is worsening, with a lack of basic necessities and violence displacing millions. International cooperation is necessary to address the ongoing crisis.",
        "links": [
            "https://www.rsschatgpt.gov/syryjska-gospodarka-na-skraju-upadku",
            "https://www.rsschatgpt.gov/wojna-w-syrii-prowadzi-do-upadku-gospodarki-kraju",
            "https://www.rsschatgpt.gov/syryjska-kryzys-humanitarny---ciągłe-wyzwania"
        ]
    },
    {
        "country": "Italy",
        "summary": "Italy: High unemployment rates of up to 20%, public debt of over 130% of GDP, and a fall in GDP are serious economic problems. Proper government action, reforms and investments are needed to ensure a stable economic future.\n\nTurkey: High unemployment, inflation and a decline in currency value are major problems. Structural reforms and focus on private sector, technology, education and training are needed. Investment in tourism and international presence will also help.",
        "links": [
            "https://www.rsschatgpt.gov/włochy-w-obliczu-kryzysu-gospodarczego---spadki-pkb-i-wzrost-bezrobocia",
            "https://www.rsschatgpt.gov/kryzys-ekonomiczny-w-turcji",
            "https://www.rsschatgpt.gov/problemy-gospodarcze-w-turcji"
        ]
    }
]
```

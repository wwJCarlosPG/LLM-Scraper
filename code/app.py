from fireworks.client import Fireworks
from pydantic_ai import Agent, Tool, RunContext
from dotenv import load_dotenv
from scraper.builtIn_adaptative_scraper import BuilInAdaptativeScraper
from scraper.model import Model

load_dotenv()
model = Model('gemini-1.5-pro-latest')
scraper = BuilInAdaptativeScraper(model)

# print(os.path.exists('code/test.html'))

html = BuilInAdaptativeScraper.clean_html('code/test.html', ['script', 'style'], True)
x = scraper.run('Extract the gretting from this page and the corresponding XPath', html)
print(x.data)

# Cargar las variables de entorno
# Verificar la clave de API
# api_key = os.getenv("GEMINI_API_KEY")
# if not api_key:
#     raise ValueError("API key not found. Make sure your .env file is correctly configured.")
# else:
#     print('TODO OK')

# agent = Agent(
#     model = 'gemini-1.5-pro',
#     system_prompt="Tell an joke"
# )

# x = agent.run_sync('I am Peter')
# print(x.data)

# client = Fireworks(api_key="fw_3ZKL6bqRbTf3SGtNKBLc9LGM")

# with open('pages/augmented_pages/bbc___12___2022.html','r') as file:
#     content = file.read()
# response = client.chat.completions.create(
# model="accounts/fireworks/models/llama-v3p3-70b-instruct",
# messages=[{
#    "role": "user",
#    "content": 'Is this an HTML?: \n'+ content,
# }],
# )

# agent = Agent(
#     system_prompt="Answer the questions like a child"
# )

# @agent.tool
# def query_fireworks(ctx: RunContext[str]):
#     pass


# print(response.choices[0].message.content)

# Para integrar un modelo alojado en **Fireworks** (o cualquier otra plataforma) con un agente de PydanticAI, debes crear un agente que sea capaz de interactuar con la API del modelo de Fireworks, enviando solicitudes y procesando las respuestas. Aquí tienes un ejemplo paso a paso:

# ---

# ### 1. **Prepara el entorno**
# Instala las dependencias necesarias si aún no lo has hecho:
# ```bash
# pip install pydantic-ai requests
# ```

# ---

# ### 2. **Define el Agente de Pydantic**
# Un agente de PydanticAI necesita herramientas (tools) o métodos para interactuar con el modelo en Fireworks. En este caso, vamos a crear una tool personalizada que haga solicitudes HTTP al modelo Fireworks.

# ```python
# from pydantic_ai import Agent, Tool, RunContext
# import requests

# class FireworksModel:
#     """Clase para interactuar con el modelo Fireworks."""
#     def __init__(self, base_url: str, api_key: str):
#         self.base_url = base_url.rstrip("/")
#         self.headers = {
#             "Authorization": f"Bearer {api_key}",
#             "Content-Type": "application/json"
#         }

#     def query_model(self, payload: dict) -> dict:
#         """Envía una consulta al modelo Fireworks."""
#         response = requests.post(f"{self.base_url}/predict", headers=self.headers, json=payload)
#         response.raise_for_status()
#         return response.json()

# # Inicializamos la instancia del modelo Fireworks
# fireworks = FireworksModel(
#     base_url="https://your-fireworks-instance.com/api/v1/models/your-model-id",
#     api_key="your-api-key"
# )

# # Tool personalizada para interactuar con Fireworks
# @Tool
# def query_fireworks(ctx: RunContext, payload: dict) -> dict:
#     """
#     Envía una consulta al modelo Fireworks y devuelve la respuesta.
#     """
#     response = fireworks.query_model(payload)
#     return {"result": response}

# # Define el agente de PydanticAI
# agent = Agent(
#     model="openai:gpt-4",
#     tools=[query_fireworks],
#     system_prompt="You can use the `query_fireworks` tool to interact with a Fireworks model. Use it to query the model as needed."
# )
# ```

# ---

# ### 3. **Utiliza el Agente**
# El agente puede ahora utilizar la herramienta `query_fireworks` para enviar datos al modelo de Fireworks y procesar la respuesta.

# ```python
# payload = {
#     "input_text": "What is the capital of France?",
#     "options": ["Paris", "London", "Berlin", "Madrid"]
# }

# # Ejecutamos el agente
# result = agent.run_sync(
#     "Use the Fireworks model to predict the answer to this question.",
#     tools=["query_fireworks"],
#     deps={"payload": payload}
# )

# print(result.data)
# ```

# ---

# ### Explicación del Flujo:
# 1. **FireworksModel**:
#    - Clase que abstrae la interacción con la API de Fireworks.  
#    - Se encarga de enviar solicitudes al endpoint `/predict` y devolver la respuesta.

# 2. **Tool personalizada**:
#    - `query_fireworks` utiliza la instancia de `FireworksModel` para enviar consultas al modelo de Fireworks.
#    - Se registra como una tool en el agente.

# 3. **Agent**:
#    - Configurado para usar GPT-4 como modelo base para generar instrucciones y herramientas personalizadas.

# 4. **Ejemplo de ejecución**:
#    - Envía una solicitud al modelo Fireworks mediante el tool `query_fireworks`.
#    - Procesa la respuesta y la devuelve como un dato estructurado.

# ---

# ### Consideraciones:
# - **Seguridad**: Asegúrate de manejar la clave API de forma segura. Puedes usar un archivo `.env` y `python-decouple` para cargarla dinámicamente.
# - **Tiempos de espera**: Configura un timeout adecuado en las solicitudes para evitar bloqueos.
# - **Logs y manejo de errores**: Implementa un registro detallado de errores para manejar fallas en la comunicación con Fireworks.

# Esta configuración te permite encapsular la lógica de interacción con Fireworks dentro del agente, lo que facilita su reutilización y mantenimiento.



# # p = random_prompt(content)
# # llm = Gemini()

# # x = llm(p)

# # print(x)
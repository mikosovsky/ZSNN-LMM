# Temat
- [OpenRouter](https://openrouter.ai/docs/quickstart)
- [Streamlit](https://docs.streamlit.io)  
- [MCP Anthropic](https://modelcontextprotocol.io/introduction)
- [FAISS](https://github.com/facebookresearch/faiss)
- [LangChain](https://python.langchain.com/docs/introduction/)
- [yfinance](https://ranaroussi.github.io/yfinance/)

# TODO
- [ ] Baza wektorowa z dodawanych plików
- [ ] Prompt template
- [ ] MCP serwer
- [ ] funkcja MCP dla yfinance
- [ ] funkcja MCP dla plotly
- [ ] funkcja MCP dla generowania raportów pdf
- [ ] dodanie cache'a
- [ ] historia chatów - baza SQLite (logowanie?)
- [ ] UI - chat + sidebar

# Workflow:
1. Użytkownik wpisuje prompt i dodaje plik
2. Pliki są czytane
3. Tworzone na ich bazie embeddingi
4. Wrzucane są do bazy wektorowej
5. Następnie baza wektorowa jest przeszukiwana na bazie wiadomości w prompt'cie
6. Budowany jest prompt: cały context rozmowy + znaleziona treść w dokumentach
7. wysyłany jest request i oczekuje na odpowiedź
8. Model ma możliwość odpytania serwera MCP o dodatkowe zasoby


## Uruchamianie:
`docker compose up --build`

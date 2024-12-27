

```Markdown
twitter-bot/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── exceptions.py      
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── twitter.py         
│   │   └── base.py   
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py         
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py     
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── tweet.py
│   │       └── user.py
│   ├── telegram/
│   │   ├── __init__.py
│   │   ├── bot.py            
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── commands.py   
│   │   │   └── callbacks.py 
│   │   └── keyboards.py    
│   └── services/
│       ├── __init__.py
│       ├── crawler_service.py 
│       └── telegram_service.py 
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_crawler/
│   └── test_telegram/
├── alembic/                
├── .env
├── requirements.txt
└── main.py
```
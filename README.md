# Chamar — Sistema de Chamados de TI

Sistema completo com React, Django REST Framework e PostgreSQL, implementado conforme `documentacao-sistema-chamados-ti (1).md`.

## Acesso

- Aplicação: http://localhost
- API: http://localhost:8001/api/v1/
- Swagger: http://localhost:8001/api/docs/
- Django Admin: http://localhost:8001/admin/
- PostgreSQL: `localhost:5433`, banco `chamar`, usuário definido no `.env`

A porta 5433 é usada porque já existe outro PostgreSQL ocupando a 5432 nesta máquina. A API usa 8001 porque a porta 8000 também já estava ocupada. Pelo endereço principal `http://localhost`, a interface encaminha `/api` internamente e funciona sem configuração adicional.

## Contas iniciais

Senha temporária comum: `Chamar@2026!`. Troque-a antes de uso fora do ambiente local.

- Administrador: `admin@chamar.local`
- Colaborador: `colaborador@chamar.local`
- Técnicos: endereços no formato `nome.sobrenome@chamar.local`, incluindo `rafael.santos@chamar.local`

## Execução

```powershell
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend
```

Para parar sem apagar o banco:

```powershell
docker compose down
```

Os dados ficam em volumes Docker persistentes. Não use `docker compose down -v` se quiser preservá-los.

## Desenvolvimento

Frontend: `cd frontend; npm run dev`. Backend nativo: configure `backend/.env` e execute `backend\.venv\Scripts\python.exe manage.py runserver 8001`. O PostgreSQL do Compose permanece disponível em `localhost:5433`.

## Operação

- Seed idempotente: `docker compose exec backend python manage.py seed_initial_data`
- Fechamento automático: `docker compose exec backend python manage.py close_resolved --days 5`
- Criar superusuário adicional: `docker compose exec backend python manage.py createsuperuser`
- Validar Django: `docker compose exec backend python manage.py check`
- Build frontend: `cd frontend; npm run lint; npm run build`

O fechamento automático deve ser agendado diariamente no ambiente de implantação. Segredos reais ficam nos arquivos `.env`, que estão ignorados pelo Git; os `.env.example` contêm apenas placeholders.
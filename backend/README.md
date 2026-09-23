# Backend Chamar

API Django/DRF do sistema de chamados.

## Variáveis

- `DJANGO_SECRET_KEY`: chave da aplicação; há fallback explícito somente para desenvolvimento.
- `DJANGO_DEBUG`: use `1` para desenvolvimento.
- `DJANGO_ALLOWED_HOSTS`: hosts separados por vírgula.
- `CORS_ALLOWED_ORIGINS`: origens separadas por vírgula; por padrão aceita localhost e 127.0.0.1 nas portas 3000 e 5173.
- `POSTGRES_HOST` (padrão `localhost`), `POSTGRES_DB` (`chamar`), `POSTGRES_USER` (`postgres`), `POSTGRES_PORT` (`5432`) e `POSTGRES_PASSWORD` (vazia).
- `INITIAL_USER_PASSWORD`: senha inicial do administrador, colaborador de demonstração e técnicos criados na primeira execução do seed. Fallback somente para desenvolvimento: `Dev@Chamar2026!`.

## Inicialização

O entrypoint executa migrations, `seed_initial_data`, coleta arquivos estáticos e inicia o Gunicorn. O seed é idempotente, reativa catálogos e não redefine senhas de usuários existentes.

## Fechamento automático

Execute `python manage.py close_resolved --days 5` para fechar chamados que permanecem resolvidos há pelo menos cinco dias. Esse comando não roda sozinho: configure sua execução periódica em um agendador (por exemplo, cron, systemd timer ou o agendador da plataforma).

## Endpoints principais

- Autenticação: `/api/v1/auth/`
- Chamados: `/api/v1/tickets/`
- Ações: `assign`, `status`, `resolve`, `cancel`, `reopen`, `delete`, `restore`, `rate`, `comments`, `attachments` e `history`
- Categorias: `/api/v1/categories/`
- Setores: `/api/v1/sectors/`
- Tipos de equipamento: `/api/v1/equipment-types/`
- Dashboard: `/api/v1/dashboard/summary/`, `/api/v1/dashboard/by-sector/`, `/api/v1/dashboard/by-technician/`, `/api/v1/dashboard/by-category/` e `/api/v1/dashboard/timeline/`
- CSV: `/api/v1/dashboard/export.csv`
- OpenAPI/Swagger: `/api/schema/` e `/api/docs/`

Uploads aceitos: PNG, JPEG e PDF de até 5 MiB, com validação do conteúdo real. Downloads exigem autenticação e visibilidade do chamado.

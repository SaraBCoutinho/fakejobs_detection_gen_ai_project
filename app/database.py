import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path("data/vagacheck.db")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id() -> str:
    return str(uuid.uuid4())


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS vagas (
                id TEXT PRIMARY KEY,
                texto_bruto TEXT,
                fonte TEXT NOT NULL,
                title TEXT,
                location TEXT,
                department TEXT,
                salary_range TEXT,
                company_profile TEXT,
                description TEXT,
                requirements TEXT,
                benefits TEXT,
                telecommuting INTEGER NOT NULL DEFAULT 0,
                has_company_logo INTEGER NOT NULL DEFAULT 0,
                has_questions INTEGER NOT NULL DEFAULT 0,
                employment_type TEXT,
                required_experience TEXT,
                required_education TEXT,
                industry TEXT,
                function TEXT,
                canal_contato TEXT,
                criado_em TEXT NOT NULL,
                usuario_id TEXT NOT NULL,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            );

            CREATE TABLE IF NOT EXISTS analises (
                id TEXT PRIMARY KEY,
                vaga_id TEXT NOT NULL UNIQUE,
                score_risco INTEGER NOT NULL,
                veredito TEXT NOT NULL,
                confianca TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                FOREIGN KEY(vaga_id) REFERENCES vagas(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS red_flags (
                id TEXT PRIMARY KEY,
                analise_id TEXT NOT NULL,
                codigo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                peso INTEGER NOT NULL,
                trecho_evidencia TEXT,
                FOREIGN KEY(analise_id) REFERENCES analises(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS denuncias (
                id TEXT PRIMARY KEY,
                vaga_id TEXT NOT NULL,
                usuario_id TEXT NOT NULL,
                motivo TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pendente',
                criado_em TEXT NOT NULL,
                FOREIGN KEY(vaga_id) REFERENCES vagas(id) ON DELETE CASCADE,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            );

            CREATE INDEX IF NOT EXISTS idx_vagas_usuario ON vagas(usuario_id);
            CREATE INDEX IF NOT EXISTS idx_analises_vaga ON analises(vaga_id);
            CREATE INDEX IF NOT EXISTS idx_flags_analise ON red_flags(analise_id);
            """
        )
        db.execute(
            """
            INSERT OR IGNORE INTO usuarios (id, nome, email, criado_em)
            VALUES ('usuario-demo', 'Usuario demo', 'demo@vagacheck.local', ?)
            """,
            (now_iso(),),
        )


def create_analysis(job: dict, result: dict) -> dict:
    init_db()
    created = now_iso()
    vaga_id = new_id()
    analise_id = new_id()
    with connect() as db:
        db.execute(
            """
            INSERT INTO vagas (
                id, texto_bruto, fonte, title, location, department, salary_range,
                company_profile, description, requirements, benefits, telecommuting,
                has_company_logo, has_questions, employment_type, required_experience,
                required_education, industry, function, canal_contato, criado_em, usuario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vaga_id,
                job.get("texto_bruto", ""),
                job.get("fonte", "outro") or "outro",
                job.get("title", ""),
                job.get("location", ""),
                job.get("department", ""),
                job.get("salary_range", ""),
                job.get("company_profile", ""),
                job.get("description", ""),
                job.get("requirements", ""),
                job.get("benefits", ""),
                int(bool(job.get("telecommuting"))),
                int(bool(job.get("has_company_logo"))),
                int(bool(job.get("has_questions"))),
                job.get("employment_type", ""),
                job.get("required_experience", ""),
                job.get("required_education", ""),
                job.get("industry", ""),
                job.get("function", ""),
                job.get("canal_contato", ""),
                created,
                "usuario-demo",
            ),
        )
        db.execute(
            """
            INSERT INTO analises (id, vaga_id, score_risco, veredito, confianca, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (analise_id, vaga_id, result["score_risco"], result["veredito"], result["confianca"], created),
        )
        db.executemany(
            """
            INSERT INTO red_flags (id, analise_id, codigo, descricao, peso, trecho_evidencia)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (new_id(), analise_id, flag["codigo"], flag["descricao"], flag["peso"], flag.get("trecho_evidencia"))
                for flag in result["red_flags"]
            ],
        )
    return get_analysis(analise_id)


def rows(query: str, params: tuple = ()) -> list[dict]:
    init_db()
    with connect() as db:
        return [dict(row) for row in db.execute(query, params).fetchall()]


def get_analysis(analysis_id: str) -> dict:
    analysis = rows(
        """
        SELECT a.*, v.title, v.fonte, v.company_profile, v.description, v.salary_range,
               v.canal_contato, v.criado_em AS vaga_criado_em
        FROM analises a
        JOIN vagas v ON v.id = a.vaga_id
        WHERE a.id = ?
        """,
        (analysis_id,),
    )
    if not analysis:
        raise KeyError(analysis_id)
    item = analysis[0]
    item["red_flags"] = rows(
        "SELECT codigo, descricao, peso, trecho_evidencia FROM red_flags WHERE analise_id = ? ORDER BY peso DESC",
        (analysis_id,),
    )
    return item


def list_analyses() -> list[dict]:
    return rows(
        """
        SELECT a.id, a.vaga_id, a.score_risco, a.veredito, a.confianca, a.criado_em,
               v.title, v.fonte, v.salary_range, v.canal_contato
        FROM analises a
        JOIN vagas v ON v.id = a.vaga_id
        ORDER BY a.criado_em DESC
        """
    )


def create_report(vaga_id: str, motivo: str) -> dict:
    init_db()
    report_id = new_id()
    created = now_iso()
    with connect() as db:
        db.execute(
            """
            INSERT INTO denuncias (id, vaga_id, usuario_id, motivo, status, criado_em)
            VALUES (?, ?, 'usuario-demo', ?, 'pendente', ?)
            """,
            (report_id, vaga_id, motivo.strip(), created),
        )
    return {"id": report_id, "vaga_id": vaga_id, "motivo": motivo.strip(), "status": "pendente", "criado_em": created}


def list_reports() -> list[dict]:
    return rows(
        """
        SELECT d.*, v.title, a.score_risco, a.veredito
        FROM denuncias d
        JOIN vagas v ON v.id = d.vaga_id
        LEFT JOIN analises a ON a.vaga_id = v.id
        ORDER BY d.criado_em DESC
        """
    )


def dashboard() -> dict:
    analyses = list_analyses()
    reports = list_reports()
    total = len(analyses)
    average = round(sum(item["score_risco"] for item in analyses) / total, 1) if total else 0
    verdicts = {"provavel_golpe": 0, "atencao": 0, "provavel_legitima": 0}
    for item in analyses:
        verdicts[item["veredito"]] = verdicts.get(item["veredito"], 0) + 1
    return {
        "total_analises": total,
        "score_medio": average,
        "denuncias": len(reports),
        "vereditos": verdicts,
        "recentes": analyses[:5],
    }

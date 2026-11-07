from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    profile = db.relationship("Profile", backref="user", uselist=False, cascade="all, delete-orphan")
    resumes = db.relationship("Resume", backref="user", cascade="all, delete-orphan")
    latex_templates = db.relationship("LatexTemplate", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(160), default="")
    phone = db.Column(db.String(60), default="")
    location = db.Column(db.String(160), default="")
    linkedin_url = db.Column(db.String(500), default="")
    portfolio_url = db.Column(db.String(500), default="")
    college_name = db.Column(db.String(255), default="")
    degree_name = db.Column(db.String(255), default="")
    program_name = db.Column(db.String(255), default="")
    enrollment_year = db.Column(db.Integer)
    graduation_year = db.Column(db.Integer)
    professional_summary = db.Column(db.Text, default="")
    skills = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def as_dict(self, email=None):
        return {
            "email": email,
            "fullName": self.full_name,
            "phone": self.phone,
            "location": self.location,
            "linkedinUrl": self.linkedin_url,
            "portfolioUrl": self.portfolio_url,
            "collegeName": self.college_name,
            "degreeName": self.degree_name,
            "programName": self.program_name,
            "enrollmentYear": self.enrollment_year,
            "graduationYear": self.graduation_year,
            "professionalSummary": self.professional_summary,
            "skills": self.skills,
        }


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    versions = db.relationship(
        "ResumeVersion",
        backref="resume",
        cascade="all, delete-orphan",
        order_by="ResumeVersion.version_number.desc()",
    )

    def as_dict(self, include_versions=True):
        data = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "createdAt": self.created_at.isoformat(),
            "latestVersion": self.versions[0].version_number if self.versions else 0,
        }
        if include_versions:
            data["versions"] = [version.as_dict() for version in self.versions]
        return data


class ResumeVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resume.id"), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(600), nullable=False)
    parsed_text = db.Column(db.Text, nullable=False, default="")
    parser_mode = db.Column(db.String(30), nullable=False, default="standard")
    notes = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("resume_id", "version_number"),)

    def as_dict(self):
        return {
            "id": self.id,
            "versionNumber": self.version_number,
            "filename": self.original_filename,
            "parserMode": self.parser_mode,
            "notes": self.notes,
            "createdAt": self.created_at.isoformat(),
            "textPreview": self.parsed_text[:220],
        }


class LatexTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    latex_code = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_latex_template_user_name"),)

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "latexCode": self.latex_code,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    resume_version_id = db.Column(db.Integer, db.ForeignKey("resume_version.id"), nullable=False)
    company_name = db.Column(db.String(255), default="")
    role_title = db.Column(db.String(255), default="")
    job_url = db.Column(db.String(1000), default="")
    job_description = db.Column(db.Text, nullable=False)
    metrics_json = db.Column(db.JSON, nullable=False)
    cover_letter = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "companyName": self.company_name,
            "roleTitle": self.role_title,
            "jobUrl": self.job_url,
            "metrics": self.metrics_json,
            "jobDescription": self.job_description,
            "coverLetter": self.cover_letter,
            "createdAt": self.created_at.isoformat(),
        }


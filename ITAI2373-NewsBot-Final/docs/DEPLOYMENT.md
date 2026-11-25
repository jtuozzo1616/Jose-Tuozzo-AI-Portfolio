# Deployment and verification

**Live academic demo:** https://final-jose-group-newsbot-intelligence-system-al984gd7vc9uzqmek.streamlit.app/

Student confirmed the application and PDF/DOCX import after the dependency fix. Anonymous public access still needs independent confirmation; external fetch was unsuccessful. The default demo uses CPU models and no paid API. Hosted uploads are processed on the server; avoid sensitive or unauthorized material.

## Reproduce deployment
1. Sign in at https://share.streamlit.io/ and authorize GitHub.
2. Repository `jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System`, branch `main`, entry `final-newsbot-2.0/app.py`.
3. Use Python 3.11 if available; deploy. The adjacent flat requirements.txt lists all dependencies, including pypdf and python-docx.
4. Open the issued URL in a private browser; exercise all five tabs and upload a text PDF and a Word file. If imports fail, check the build log and reboot after dependency changes.

[Hosted dependency and 38-test verification](https://github.com/jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System/actions/runs/45698267399). For Docker see [Dockerfile.web](../Dockerfile.web) and the root render.yaml. For limitations and optional neural assets see [user guide](user_guide.md).

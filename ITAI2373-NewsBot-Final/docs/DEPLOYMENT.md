# Public deployment

The Streamlit application is ready for a free Community Cloud deployment. Account authorization is required; a public app URL is not asserted until the host returns it and a browser smoke test passes.

1. Sign in at https://share.streamlit.io/ using GitHub.
2. Create an app from an existing repository.
3. Repository: `jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System`; branch: `main`; main file: `final-newsbot-2.0/app.py`.
4. Use Python 3.11 in advanced settings. Deploy. The adjacent requirements.txt installs the application dependencies.
5. Copy the issued URL, open it in a private browser and exercise all five tabs. The bundled fictional data is safe to display publicly; do not upload confidential or copyrighted content.

For a free Render alternative, the root render.yaml defines a Docker service, with health check at /_stcore/health. Authorize the repo and approve the free service before deployment. The default public instance deliberately uses the lightweight local classifier rather than downloading neural models. No paid API is required.

The neural option is documented separately and should be demonstrated locally or using the actual CI evidence, not advertised as active in the lightweight hosted demo.

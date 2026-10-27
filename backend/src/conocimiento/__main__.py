from conocimiento.cli import main
from conocimiento.config import cargar_archivo_env

cargar_archivo_env()
raise SystemExit(main())

from fastapi import APIRouter

from routers.pages.index import router as index_router
from routers.pages.login import router as login_router
from routers.pages.logout import router as logout_router
from routers.pages.projects import router as projects_router
from routers.pages.export import router as export_router
from routers.pages.tasks import router as tasks_router
from routers.pages.generic import router as generic_router

# Create a combined router with prefix "/ui" and tag "pages"
router = APIRouter(
    prefix="/ui",
    tags=["pages"],
)

# Include all the individual routers
router.include_router(index_router)
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(projects_router)
router.include_router(export_router)
router.include_router(tasks_router)
router.include_router(
    generic_router
)  # This should be included last as it has a catch-all route

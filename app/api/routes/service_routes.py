from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.service_repository import ServiceRepository
from app.schemas.service_schema import ServiceCreate, ServiceResponse, ServiceUpdate
from app.services.service_catalog_service import ServiceCatalogService

router = APIRouter(
    prefix="/services",
    tags=["Services"]
)


def get_service_catalog_service(db: Session = Depends(get_db)) -> ServiceCatalogService:
    repository = ServiceRepository(db)
    return ServiceCatalogService(repository)


@router.get("", response_model=list[ServiceResponse])
def get_services(
        search: str | None = None,
        service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    return service.get_all_services(search=search)


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
        service_id: int,
        service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    return service.get_service_by_id(service_id)


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
        request: ServiceCreate,
        service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    return service.create_service(
        naziv_usluge=request.NazivUsluge,
        opis=request.Opis,
        trajanje=request.Trajanje,
        cijena=request.Cijena
    )


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
        service_id: int,
        request: ServiceUpdate,
        service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    return service.update_service(
        service_id=service_id,
        naziv_usluge=request.NazivUsluge,
        opis=request.Opis,
        trajanje=request.Trajanje,
        cijena=request.Cijena
    )


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
        service_id: int,
        service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    service.delete_service(service_id)

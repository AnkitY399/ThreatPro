"""
ThreatPro - Geospatial Intelligence Router
Cybercrime hotspot mapping, DBSCAN clustering, and patrol route optimization.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models.schemas import GeoLocation, GeoLocationResponse, PatrolRoute, PatrolRouteResponse
from ..core.graph_builder import geospatial_engine

router = APIRouter(prefix="/api/v1/geospatial", tags=["Geospatial"])


@router.post("/seed")
def seed_geodata(count: int = Query(30, ge=5, le=100), db: Session = Depends(get_db)):
    """Seed the geospatial database with synthetic cybercrime incident locations."""
    geospatial_engine.seed_locations(count=count)

    # Store in database
    for loc in geospatial_engine.locations:
        existing = db.query(GeoLocation).filter(
            GeoLocation.location_id == loc["location_id"]
        ).first()
        if not existing:
            record = GeoLocation(
                location_id=loc["location_id"],
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                location_name=loc["location_name"],
                city=loc["city"],
                state=loc["state"],
                incident_count=loc["incident_count"],
                risk_level=loc["risk_level"],
            )
            db.add(record)
    db.commit()

    return {
        "status": "seeded",
        "locations_count": len(geospatial_engine.locations),
    }


@router.get("/locations", response_model=List[GeoLocationResponse])
def get_locations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all geospatial locations."""
    return db.query(GeoLocation).offset(skip).limit(limit).all()


@router.post("/cluster")
def run_clustering(
    eps: Optional[float] = Query(None, description="DBSCAN epsilon (km)"),
    min_samples: Optional[int] = Query(None, description="Minimum points for core cluster"),
    db: Session = Depends(get_db),
):
    """
    Run DBSCAN clustering on loaded geospatial data to identify cybercrime hotspots.
    """
    # Load locations from DB if engine is empty
    if not geospatial_engine.locations:
        db_locations = db.query(GeoLocation).all()
        geospatial_engine.locations = [
            {
                "location_id": loc.location_id,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "location_name": loc.location_name,
                "city": loc.city,
                "state": loc.state,
                "incident_count": loc.incident_count,
                "risk_level": loc.risk_level,
                "cluster_id": None,
            }
            for loc in db_locations
        ]

    if not geospatial_engine.locations:
        raise HTTPException(status_code=400, detail="No geospatial data loaded. POST /seed first.")

    clusters = geospatial_engine.run_dbscan(eps=eps, min_samples=min_samples)
    hotspots = geospatial_engine.get_hotspots()

    # Update cluster IDs in database
    for cluster_id, locations in geospatial_engine.clusters.items():
        for loc in locations:
            db.query(GeoLocation).filter(
                GeoLocation.location_id == loc["location_id"]
            ).update({"cluster_id": cluster_id})
    db.commit()

    return {
        "clusters_found": len(clusters),
        "clusters": [{"id": cid, "size": len(locs)} for cid, locs in clusters.items()],
        "hotspots": hotspots,
    }


@router.get("/hotspots")
def get_hotspots():
    """Get identified cybercrime hotspot clusters."""
    hotspots = geospatial_engine.get_hotspots()
    return {"hotspots": hotspots, "count": len(hotspots)}


@router.post("/patrol-optimize", response_model=PatrolRouteResponse)
def optimize_patrol_route(
    generations: Optional[int] = Query(None, ge=10, le=500),
    db: Session = Depends(get_db),
):
    """
    Run genetic algorithm optimization for law enforcement patrol routes.
    """
    hotspots = geospatial_engine.get_hotspots()
    if len(hotspots) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 hotspots for route optimization. Run clustering first.",
        )

    # Get hotspot centroids
    centers = [(h["centroid_lat"], h["centroid_lon"]) for h in hotspots]

    result = geospatial_engine.optimize_patrol_route(
        hotspot_centers=centers,
        generations=generations,
    )

    # Store patrol route in database
    route_record = PatrolRoute(
        route_id=result["route_id"],
        waypoints=result["waypoints"],
        total_distance_km=result["total_distance_km"],
        estimated_time_min=result["estimated_time_min"],
        coverage_score=result["coverage_score"],
        hotspots_covered=result["hotspots_covered"],
        generation=result["generation"],
    )
    db.add(route_record)
    db.commit()
    db.refresh(route_record)

    return route_record


@router.get("/routes", response_model=List[PatrolRouteResponse])
def get_patrol_routes(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get all generated patrol routes."""
    return (
        db.query(PatrolRoute)
        .order_by(PatrolRoute.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/routes/{route_id}", response_model=PatrolRouteResponse)
def get_patrol_route(route_id: str, db: Session = Depends(get_db)):
    """Get a specific patrol route by ID."""
    route = db.query(PatrolRoute).filter(PatrolRoute.route_id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
    return route


@router.get("/stats")
def get_geospatial_stats(db: Session = Depends(get_db)):
    """Get geospatial analytics statistics."""
    locations = db.query(GeoLocation).count()
    routes = db.query(PatrolRoute).count()
    cities = db.query(GeoLocation.city).distinct().count()
    total_incidents = db.query(GeoLocation.incident_count).all()

    return {
        "total_locations": locations,
        "total_cities": cities,
        "total_incidents": sum(i[0] for i in total_incidents) if total_incidents else 0,
        "patrol_routes_generated": routes,
        "clusters_active": len(geospatial_engine.clusters),
    }
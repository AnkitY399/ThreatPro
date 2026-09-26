'use client';

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface Location {
  id: number;
  location_id: string;
  latitude: number;
  longitude: number;
  location_name: string;
  city: string;
  state: string;
  incident_count: number;
  risk_level: number;
}

export default function GeoMap({ locations }: { locations: Location[] }) {
  return (
    <div className="w-full h-[420px] rounded-xl overflow-hidden border border-white/[0.06]">
      <MapContainer
        center={[22.5, 78.9]}
        zoom={5}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {locations.map((location) => (
          <CircleMarker
            key={location.id}
            center={[location.latitude, location.longitude]}
            radius={10}
          >
            <Popup>
              <strong>{location.location_name}</strong>
              <br />
              {location.city}, {location.state}
              <br />
              Incidents: {location.incident_count}
              <br />
              Risk: {location.risk_level}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
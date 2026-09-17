import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Droplets, ShieldCheck, Check, PlusCircle, HardHat } from 'lucide-react';
import './App.css';

const CMC_CENTER = [12.9165, 79.1325];

// Custom Map Marker Icon
const createCustomIcon = (isBlinking, riskScore) => {
  const color = riskScore >= 0.50 ? '#dc2626' : riskScore >= 0.35 ? '#f97316' : '#eab308';
  return L.divIcon({
    className: 'custom-map-pin',
    html: `<div class="pin-marker ${isBlinking ? 'blink-active' : ''}" style="background-color: ${color}"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
};

function MapController({ center }) {
  const map = useMap();
  React.useEffect(() => {
    if (center) map.flyTo(center, 15);
  }, [center, map]);
  return null;
}

export default function App() {
  const [rainfall, setRainfall] = useState(120);
  const [drains, setDrains] = useState([]);
  const [desiltedDrainIds, setDesiltedDrainIds] = useState([]);
  const [activeDrainMap, setActiveDrainMap] = useState(null);
  
  // Pending Queue Tickets
  const [tickets, setTickets] = useState([
    { id: '1', drain_id: 'CMC_DR_035', status: 'Pending' }
  ]);

  // Modal State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [newDrainId, setNewDrainId] = useState('');
  const [newBlockage, setNewBlockage] = useState(80);

  // Initial postgis / mock spatial data fetch
  useEffect(() => {
    fetchPostGISDrains();
  }, []);

  const fetchPostGISDrains = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/drains/spatial');
      const result = await response.json();
      if (result.status === 'success' && result.data?.length > 0) {
        setDrains(result.data);
      } else {
        throw new Error('Empty response');
      }
    } catch (error) {
      // Default fallback dataset if PostGIS backend is offline
      setDrains([
        { drain_id: 'GANDHI NAGAR', blockage_ratio: '0.91', width_m: 1.5, geometry: { type: 'LineString', coordinates: [[79.1325, 12.9165], [79.1335, 12.9175]] } },
        { drain_id: 'CMC_DR_035', blockage_ratio: '0.85', width_m: 1.5, geometry: { type: 'LineString', coordinates: [[79.1340, 12.9150], [79.1350, 12.9160]] } },
        { drain_id: 'CMC_DR_009', blockage_ratio: '0.80', width_m: 1.5, geometry: { type: 'LineString', coordinates: [[79.1310, 12.9180], [79.1320, 12.9190]] } },
        { drain_id: 'CMC_DR_002', blockage_ratio: '0.65', width_m: 1.5, geometry: { type: 'LineString', coordinates: [[79.1300, 12.9140], [79.1310, 12.9150]] } },
        { drain_id: 'CMC_DR_001', blockage_ratio: '0.37', width_m: 1.5, geometry: { type: 'LineString', coordinates: [[79.1280, 12.9130], [79.1290, 12.9140]] } }
      ]);
    }
  };

  // Dynamic Risk & Threat Calculation tied strictly to Rainfall Slider
  const calculateMetrics = () => {
    const activeDrains = drains.map(d => {
      const isDesilted = desiltedDrainIds.includes(d.drain_id);
      const rawBlockage = parseFloat(d.blockage_ratio) || 0;
      const effectiveBlockage = isDesilted ? 0.05 : rawBlockage;
      
      // Dynamic Risk Formula: Scales cleanly as rainfall slider changes
      const riskScore = (effectiveBlockage * (rainfall / 200)).toFixed(2);

      return { ...d, effectiveBlockage, riskScore };
    });

    const avgRisk = activeDrains.length > 0 
      ? (activeDrains.reduce((acc, curr) => acc + parseFloat(curr.riskScore), 0) / activeDrains.length) 
      : 0;
    const bottlenecks = activeDrains.filter(d => parseFloat(d.riskScore) >= 0.35).length;

    return { activeDrains, avgRisk, bottlenecks };
  };

  const { activeDrains, avgRisk, bottlenecks } = calculateMetrics();

  const handleRainfallChange = (e) => {
    setRainfall(Number(e.target.value));
  };

  const toggleDesilt = (drainId) => {
    setDesiltedDrainIds(prev => 
      prev.includes(drainId) ? prev.filter(id => id !== drainId) : [...prev, drainId]
    );
  };

  const handleResolveTicket = (ticketId, drainId) => {
    setTickets(prev => prev.filter(t => t.id !== ticketId));
    if (!desiltedDrainIds.includes(drainId)) {
      setDesiltedDrainIds(prev => [...prev, drainId]);
    }
  };

  const handleDispatch = (drainId) => {
    if (tickets.some(t => t.drain_id === drainId)) return;
    const newTicket = { id: Date.now().toString(), drain_id: drainId, status: 'Pending' };
    setTickets(prev => [...prev, newTicket]);
  };

  // Bulletproof Field Entry Saver
  const handleSaveFieldData = async () => {
    if (!newDrainId.trim()) return;

    let startLat = 12.9165 + (Math.random() - 0.5) * 0.008;
    let startLng = 79.1325 + (Math.random() - 0.5) * 0.008;

    try {
      const geoRes = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(newDrainId + ' Vellore')}`
      );
      if (geoRes.ok) {
        const geoData = await geoRes.json();
        if (geoData && geoData.length > 0) {
          startLat = parseFloat(geoData[0].lat);
          startLng = parseFloat(geoData[0].lon);
        }
      }
    } catch (err) {
      console.warn('Geocoding offline, generated coordinates locally');
    }

    const newDrainObj = {
      drain_id: newDrainId.toUpperCase(),
      blockage_ratio: (newBlockage / 100).toFixed(2),
      width_m: 1.50,
      geometry: {
        type: 'LineString',
        coordinates: [
          [startLng, startLat],
          [startLng + 0.001, startLat + 0.001]
        ]
      }
    };

    // Update state synchronously so modal disappears immediately
    setDrains(prev => [newDrainObj, ...prev]);
    setShowUploadModal(false);
    setNewDrainId('');
    setNewBlockage(80);

    // Sync to backend asynchronously
    try {
      await fetch('http://localhost:5000/api/drains/spatial', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drain_id: newDrainObj.drain_id,
          blockage_ratio: newDrainObj.blockage_ratio,
          width_m: newDrainObj.width_m,
          start_coords: [startLng, startLat],
          end_coords: [startLng + 0.001, startLat + 0.001]
        })
      });
    } catch (err) {
      console.log('Stored locally in component memory');
    }
  };

  // Dynamic Threat Badge Assignment Function
  const getThreatBadge = (riskScore, effectiveBlockage) => {
    if (effectiveBlockage <= 0.05) {
      return <span className="badge badge-green">CLEARED</span>;
    }

    const score = parseFloat(riskScore);

    if (score >= 0.50) return <span className="badge badge-red">CRITICAL</span>;
    if (score >= 0.35) return <span className="badge badge-orange">HIGH</span>;
    if (score >= 0.18) return <span className="badge badge-yellow">MEDIUM</span>;
    return <span className="badge badge-blue">LOW</span>;
  };

  return (
    <div className="dashboard-container">
      <header className="header">
        <div>
          <h1>CivicTwin</h1>
          <p>CMC Zone Drainage & Flood Command (GNN & PostGIS Powered)</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button className="btn-secondary" onClick={() => setShowUploadModal(true)}>
            <PlusCircle size={15} /> Add Drain Details
          </button>
          <span className="status-badge">System Active</span>
        </div>
      </header>

      <div className="grid-layout">
        {/* Sidebar Controls */}
        <div className="sidebar">
          <div className="card">
            <h3><Droplets size={16} /> Storm Simulation</h3>
            <div className="control-group">
              <label>Rainfall: <strong>{rainfall} mm/hr</strong></label>
              <input
                type="range"
                min="20"
                max="200"
                step="10"
                value={rainfall}
                onChange={handleRainfallChange}
              />
            </div>
          </div>

          <div className="card">
            <h3><ShieldCheck size={16} /> Dynamic Metrics</h3>
            <div className="metric-box">
              <p>Network Flood Risk</p>
              <h2 className={avgRisk > 0.4 ? 'risk-high' : 'risk-low'}>
                {(avgRisk * 100).toFixed(0)}%
              </h2>
            </div>

            {desiltedDrainIds.length > 0 && (
              <div className="metric-box" style={{ borderColor: '#16a34a', backgroundColor: '#f0fdf4' }}>
                <p style={{ color: '#16a34a', fontWeight: 'bold' }}>Desilting Sim Impact</p>
                <h3 style={{ color: '#15803d', margin: '4px 0' }}>
                  {desiltedDrainIds.length} Channel(s) Cleaned
                </h3>
                <span style={{ fontSize: '0.8rem', color: '#166534' }}>
                  Topology Risk Mitigated
                </span>
              </div>
            )}

            <div className="metric-box">
              <p>Critical Bottlenecks</p>
              <h2>{bottlenecks} Drains</h2>
            </div>
          </div>
        </div>

        {/* Main Interface Content */}
        <div className="main-content">
          <div className="card">
            <h3>CMC Area Map ({activeDrains.length} PostGIS Conduits Logged)</h3>
            <MapContainer center={CMC_CENTER} zoom={14} style={{ height: '300px', width: '100%', borderRadius: '8px' }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {activeDrainMap && <MapController center={activeDrainMap.coords} />}
              
              {activeDrains.map((drain) => {
                const pipeCoordinates = drain.geometry?.coordinates?.map(coord => [coord[1], coord[0]]) || [];
                const isHighRisk = parseFloat(drain.riskScore) >= 0.35;
                const isSelected = activeDrainMap?.id === drain.drain_id;

                return (
                  <React.Fragment key={drain.drain_id}>
                    {pipeCoordinates.length > 0 && (
                      <>
                        <Polyline
                          positions={pipeCoordinates}
                          pathOptions={{
                            color: isHighRisk ? '#dc2626' : '#2563eb',
                            weight: (parseFloat(drain.width_m) || 1.5) * 3,
                            dashArray: isHighRisk ? '6, 6' : null
                          }}
                        >
                          <Popup>
                            <strong>Channel ID: {drain.drain_id}</strong><br />
                            Width: {drain.width_m || 1.5}m<br />
                            Effective Blockage: {(drain.effectiveBlockage * 100).toFixed(0)}%<br />
                            Dynamic Risk Score: {drain.riskScore}
                          </Popup>
                        </Polyline>

                        <Marker
                          position={pipeCoordinates[0]}
                          icon={createCustomIcon(isSelected, parseFloat(drain.riskScore))}
                        >
                          <Popup>
                            <strong>{drain.drain_id} Junction</strong>
                          </Popup>
                        </Marker>
                      </>
                    )}
                  </React.Fragment>
                );
              })}
            </MapContainer>
          </div>

          {/* Drains Priority Table */}
          <div className="card">
            <h3>Priority Drains</h3>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Desilt Sim</th>
                  <th>Drain ID</th>
                  <th>Blockage</th>
                  <th>Threat</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {activeDrains.map((drain) => {
                  const pipeCoords = drain.geometry?.coordinates?.map(coord => [coord[1], coord[0]]) || [];
                  const centerPoint = pipeCoords[0] || CMC_CENTER;

                  return (
                    <tr
                      key={drain.drain_id}
                      onClick={() => setActiveDrainMap({ id: drain.drain_id, coords: centerPoint })}
                      className="clickable-row"
                    >
                      <td>
                        <input
                          type="checkbox"
                          checked={desiltedDrainIds.includes(drain.drain_id)}
                          onChange={() => toggleDesilt(drain.drain_id)}
                        />
                      </td>
                      <td><strong>{drain.drain_id}</strong></td>
                      <td>{(drain.effectiveBlockage * 100).toFixed(0)}%</td>
                      <td>
                        {getThreatBadge(drain.riskScore, drain.effectiveBlockage)}
                      </td>
                      <td>
                        <button className="btn-direct" onClick={(e) => { e.stopPropagation(); handleDispatch(drain.drain_id); }}>
                          <HardHat size={12} /> Dispatch
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Active Maintenance Queue */}
          <div className="card">
            <h3>Active Queue ({tickets.length})</h3>
            {tickets.length === 0 ? (
              <p className="subtext">Queue clear. No pending maintenance orders.</p>
            ) : (
              <ul className="ticket-list">
                {tickets.map((t) => (
                  <li key={t.id} className="ticket-item">
                    <span><strong>{t.drain_id}</strong> — Cleaning Assigned</span>
                    <button className="btn-resolve-direct" onClick={() => handleResolveTicket(t.id, t.drain_id)}>
                      <Check size={14} /> Mark Cleared & Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Add Survey Modal */}
      {showUploadModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3>Add Ground Survey Details</h3>
            <p className="subtext">Register open drain inspection data in the CMC Zone.</p>
            
            <div className="control-group" style={{ marginBottom: '12px' }}>
              <label>Drain ID / Location Name</label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g., Gandhi Nagar Main Street"
                value={newDrainId}
                onChange={(e) => setNewDrainId(e.target.value)}
              />
            </div>

            <div className="control-group" style={{ marginBottom: '16px' }}>
              <label>Observed Blockage: <strong>{newBlockage}%</strong></label>
              <input
                type="range"
                min="10"
                max="100"
                value={newBlockage}
                onChange={(e) => setNewBlockage(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button className="btn-secondary" onClick={() => setShowUploadModal(false)}>Cancel</button>
              <button className="btn-direct" onClick={handleSaveFieldData}>Save Entry</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
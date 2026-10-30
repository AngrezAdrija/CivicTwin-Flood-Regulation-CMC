const express = require('express');
const cors = require('cors');
require('dotenv').config();
const pool = require('./db');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Import Routes
const simulationRoutes = require('./routes/simulationRoutes');
const ticketRoutes = require('./routes/ticketRoutes');

app.use('/api/simulation', simulationRoutes);
app.use('/api/tickets', ticketRoutes);

// Fetch PostGIS GeoJSON Spatial Route
app.get('/api/drains/spatial', async (req, res) => {
  try {
    const query = `
      SELECT 
        c.drain_id,
        c.blockage_ratio,
        c.width_m,
        c.start_node_id,
        c.end_node_id,
        ST_AsGeoJSON(c.geom)::json AS geometry
      FROM drain_conduits c;
    `;
    const { rows } = await pool.query(query);
    res.json({ status: 'success', data: rows });
  } catch (err) {
    console.error('PostGIS Query Error:', err.message);
    res.status(500).json({ error: 'Database query failed' });
  }
});
// PostGIS Route: Insert New Ground Survey Drain Conduit
  app.post('/api/drains/spatial', async (req, res) => {
    const { drain_id, blockage_ratio, width_m, start_coords, end_coords } = req.body;
    
    try {
      const query = `
        INSERT INTO drain_conduits (drain_id, blockage_ratio, width_m, geom)
        VALUES (
          $1, 
          $2, 
          $3, 
          ST_SetSRID(ST_MakeLine(ST_MakePoint($4, $5), ST_MakePoint($6, $7)), 4326)
        )
        RETURNING drain_id, blockage_ratio, width_m, ST_AsGeoJSON(geom)::json AS geometry;
      `;
      
      const values = [
        drain_id,
        blockage_ratio,
        width_m || 1.5,
        start_coords[0], // start lng
        start_coords[1], // start lat
        end_coords[0],   // end lng
        end_coords[1]    // end lat
      ];

      const { rows } = await pool.query(query, values);
      res.status(201).json({ status: 'success', data: rows[0] });
    } catch (err) {
      console.error('PostGIS Insert Error:', err.message);
      res.status(500).json({ error: 'Failed to insert conduit into PostGIS' });
    }
  });
// Single Unified Server Initialization
const PORT = process.env.PORT || 5000;
// PostGIS Route: Insert New Ground Survey Drain Conduit
app.post('/api/drains/spatial', async (req, res) => {
  const { drain_id, blockage_ratio, width_m, start_coords, end_coords } = req.body;
  
  try {
    const query = `
      INSERT INTO drain_conduits (drain_id, blockage_ratio, width_m, geom)
      VALUES (
        $1, 
        $2, 
        $3, 
        ST_SetSRID(ST_MakeLine(ST_MakePoint($4, $5), ST_MakePoint($6, $7)), 4326)
      )
      RETURNING drain_id, blockage_ratio, width_m, ST_AsGeoJSON(geom)::json AS geometry;
    `;
    
    const values = [
      drain_id,
      blockage_ratio,
      width_m || 1.5,
      start_coords[0], // start lng
      start_coords[1], // start lat
      end_coords[0],   // end lng
      end_coords[1]    // end lat
    ];

    const { rows } = await pool.query(query, values);
    res.status(201).json({ status: 'success', data: rows[0] });
  } catch (err) {
    console.error('PostGIS Insert Error:', err.message);
    res.status(500).json({ error: 'Failed to insert conduit into PostGIS' });
  }
});
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT} with PostGIS spatial integration`);
});

// PostGIS Route: Extract Spatial Graph Adjacency Matrix
  app.get('/api/drains/adjacency', async (req, res) => {
    try {
      const query = `
        SELECT 
          a.drain_id AS source_id, 
          b.drain_id AS target_id
        FROM drain_conduits a
        JOIN drain_conduits b 
          ON a.drain_id != b.drain_id 
          AND ST_DWithin(a.geom, b.geom, 0.0001);
      `;
      const { rows } = await pool.query(query);
      res.status(200).json({ status: 'success', adjacency: rows });
    } catch (err) {
      console.error('Adjacency Extraction Error:', err.message);
      res.status(500).json({ error: 'Failed to extract network topology' });
    }
  });
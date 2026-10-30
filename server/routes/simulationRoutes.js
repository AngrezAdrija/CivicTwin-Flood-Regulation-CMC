const express = require('express');
const router = express.Router();
const axios = require('axios');

const PYTHON_ENGINE_URL = process.env.PYTHON_ENGINE_URL || 'http://localhost:5000';

// GET Top 10 Critical Drains
router.get('/top10', async (req, res) => {
    try {
        const response = await axios.get(`${PYTHON_ENGINE_URL}/api/py/top10-critical`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Failed to fetch top 10 critical drains from Python engine." });
    }
});

// GET Drains by Ward
router.get('/ward/:wardNum', async (req, res) => {
    try {
        const response = await axios.get(`${PYTHON_ENGINE_URL}/api/py/ward/${req.params.wardNum}`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Failed to fetch ward drains." });
    }
});

// POST Mark Drain Cleaned
router.post('/clean', async (req, res) => {
    try {
        const response = await axios.post(`${PYTHON_ENGINE_URL}/api/py/mark-cleaned`, req.body);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Failed to mark drain as cleaned." });
    }
});

// POST Simulate Rainfall (Range: 20 - 200 mm/hr)
router.post('/simulate', async (req, res) => {
    try {
        const response = await axios.post(`${PYTHON_ENGINE_URL}/api/py/simulate-rainfall`, req.body);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Failed to run rainfall simulation." });
    }
});

module.exports = router;
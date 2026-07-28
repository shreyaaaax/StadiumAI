const BASE = "http://localhost:8000";

let rateLimitListeners = [];

export function subscribeToRateLimit(cb) {
    rateLimitListeners.push(cb);
    return () => {
        rateLimitListeners = rateLimitListeners.filter(l => l !== cb);
    };
}

async function request(endpoint, options = {}) {
    const url = `${BASE}${endpoint}`;
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };
    
    const config = {
        ...options,
        headers,
    };

    try {
        const response = await fetch(url, config);
        
        if (response.status === 429) {
            rateLimitListeners.forEach(cb => cb(true));
        } else if (response.ok) {
            rateLimitListeners.forEach(cb => cb(false));
        }

        if (!response.ok) {
            let errorText = "API request failed";
            try {
                const errBody = await response.json();
                errorText = errBody.detail || JSON.stringify(errBody);
            } catch (_) {}
            throw new Error(`[${response.status}] ${errorText}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Fetch API Error for ${endpoint}:`, error);
        throw error;
    }
}

export async function sendChat(message, venueId, language) {
    return request("/chat", {
        method: "POST",
        body: JSON.stringify({ message, venue_id: venueId, language }),
    });
}

export async function getNavigation(fromLocation, toLocation, venueId, language, accessible = false) {
    return request("/navigation", {
        method: "POST",
        body: JSON.stringify({
            from_location: fromLocation,
            to_location: toLocation,
            venue_id: venueId,
            language,
            accessible,
        }),
    });
}

export async function getCrowd(venueId, phase = "during") {
    // API endpoint is GET /crowd/{venue_id}?phase={phase}
    const cleanId = venueId.replace("venue-", "");
    return request(`/crowd/${cleanId}?phase=${phase}`, {
        method: "GET",
    });
}

export async function getCrowdPredict(venueId, currentPhase, query = "Which areas to avoid right now?") {
    const cleanId = venueId.replace("venue-", "");
    return request("/crowd/predict", {
        method: "POST",
        body: JSON.stringify({
            venue_id: cleanId,
            current_phase: currentPhase,
            query
        }),
    });
}

export async function getTransport(venueId, matchTime24h, currentTime24h, origin, language) {
    const cleanId = venueId.replace("venue-", "");
    return request("/transport/recommend", {
        method: "POST",
        body: JSON.stringify({
            venue_id: cleanId,
            match_time_24h: matchTime24h,
            current_time_24h: currentTime24h,
            origin,
            language,
        }),
    });
}

export async function staffQuery(question, role, venueId) {
    return request("/staff/query", {
        method: "POST",
        body: JSON.stringify({ question, role, venue_id: venueId }),
    });
}

export async function staffIncidentReport(description, location, severity) {
    return request("/staff/incident_report", {
        method: "POST",
        body: JSON.stringify({ description, location, severity: parseInt(severity, 10) }),
    });
}

// Sustainability
export async function getSustainability(venueId, phase = "during") {
    return request(`/sustainability/${venueId}?phase=${phase}`, {
        method: "GET",
    });
}

export async function postSustainabilityInsight(venueId, question, phase = "during") {
    return request("/sustainability/insight", {
        method: "POST",
        body: JSON.stringify({ venue_id: venueId, question, phase }),
    });
}

export async function getSustainabilityFanScore(venueId) {
    return request(`/sustainability/${venueId}/fan_score`, {
        method: "GET",
    });
}

// Accessibility
export async function getAccessibilityAssist(query, venueId, language, need) {
    return request("/accessibility/assist", {
        method: "POST",
        body: JSON.stringify({ query, venue_id: venueId, language, need }),
    });
}

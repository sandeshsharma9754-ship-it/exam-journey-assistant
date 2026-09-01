import { useMemo, useState } from "react";
import "./App.css";

const API_BASE = "https://exam-journey-assistant-2.onrender.com";

type AnyObject = Record<string, any>;
type TravelMode = "car" | "bus" | "train";
type JourneyStage = "plan" | "travel" | "arrive" | "exam" | "home";

function App() {
  const [name, setName] = useState("");
  const [examName, setExamName] = useState("");
  const [examDate, setExamDate] = useState("");
  const [reportingTime, setReportingTime] = useState("");
  const [gateClosingTime, setGateClosingTime] = useState("");
  const [centreName, setCentreName] = useState("");
  const [centreAddress, setCentreAddress] = useState("");
  const [city, setCity] = useState("");
  const [currentLocation, setCurrentLocation] = useState("");

  const [travelMode, setTravelMode] = useState<TravelMode>("car");
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsStatus, setGpsStatus] = useState("");

  const [journey, setJourney] = useState<AnyObject | null>(null);
  const [centre, setCentre] = useState<AnyObject | null>(null);
  const [support, setSupport] = useState<AnyObject | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Delay simulation
  const [delayMinutes, setDelayMinutes] = useState(0);
  const [delayResult, setDelayResult] = useState<AnyObject | null>(null);
  const [delayLoading, setDelayLoading] = useState(false);
  const [delayError, setDelayError] = useState("");

  const [stage, setStage] = useState<JourneyStage>("plan");
  const [showPostArrival, setShowPostArrival] = useState(false);
  const [showExamComplete, setShowExamComplete] = useState(false);
  const [examSuccessful, setExamSuccessful] = useState<boolean | null>(null);
  const [returnJourney, setReturnJourney] = useState(false);

  const [lastGps, setLastGps] = useState<{
    lat: number;
    lng: number;
  } | null>(null);

  function formatValue(value: any): string {
    if (value === undefined || value === null || value === "") {
      return "Not available";
    }

    if (typeof value === "string") return value;
    if (typeof value === "number") return String(value);

    if (Array.isArray(value)) {
      return value.map((item) => formatValue(item)).join(", ");
    }

    if (typeof value === "object") {
      return (
        value.message ||
        value.msg ||
        value.description ||
        value.detail ||
        JSON.stringify(value)
      );
    }

    return String(value);
  }

  function formatMinutes(value: any): string {
    if (value === undefined || value === null || value === "") {
      return "Not available";
    }

    const minutes = Number(value);

    if (Number.isNaN(minutes)) {
      return formatValue(value);
    }

    if (minutes < 60) return `${minutes} min`;

    const hours = Math.floor(minutes / 60);
    const remaining = minutes % 60;

    if (remaining === 0) return `${hours} hr`;

    return `${hours} hr ${remaining} min`;
  }

  function formatDateTime(value: any): string {
    if (!value) return "Not available";

    const raw = String(value);

    const date = new Date(
      raw.includes(" ") ? raw.replace(" ", "T") : raw
    );

    if (Number.isNaN(date.getTime())) return raw;

    return date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function getRiskClass(risk: any): string {
    const value = String(risk || "UNKNOWN").toUpperCase();

    if (value.includes("CRITICAL")) return "risk-critical";
    if (value.includes("HIGH")) return "risk-high";
    if (value.includes("MEDIUM")) return "risk-medium";
    if (value.includes("LOW")) return "risk-low";

    return "risk-unknown";
  }

  function getErrorMessage(data: AnyObject): string {
    if (!data?.detail) {
      return "Unable to generate the journey plan.";
    }

    const detail = data.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          return item?.msg || item?.message || JSON.stringify(item);
        })
        .join(" | ");
    }

    if (typeof detail === "object") {
      return (
        detail.message ||
        detail.msg ||
        detail.detail ||
        JSON.stringify(detail)
      );
    }

    return String(detail);
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setJourney(null);
    setCentre(null);
    setSupport(null);

    // Reset delay simulation
    setDelayMinutes(0);
    setDelayResult(null);
    setDelayError("");

    setStage("plan");
    setShowPostArrival(false);
    setShowExamComplete(false);
    setExamSuccessful(null);
    setReturnJourney(false);
    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/exam/complete-plan`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            starting_location: currentLocation,
            exam_centre: centreName,
            exam_date: examDate,
            reporting_time: reportingTime,
            gate_closing_time: gateClosingTime,
            local_travel_minutes: 0,
            transport_delay_minutes: 0,
            departure_time: null,
            centre_name: centreName,
            centre_address: centreAddress,
            centre_city: city,
            centre_latitude: null,
            centre_longitude: null,
            admit_card_data: null,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(getErrorMessage(data));
      }

      if (!data.exam_plan) {
        throw new Error(
          "The server returned an incomplete exam plan."
        );
      }

      setJourney(data.exam_plan.journey || null);
      setCentre(data.exam_plan.centre || null);
      setSupport(data.exam_plan.student_support || null);
    } catch (err) {
      if (err instanceof TypeError) {
        setError(
          "Unable to connect to the backend. Please check the online server."
        );
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // DELAY SIMULATION
  // ============================================================

  async function simulateDelay(minutes: number) {
    if (!journey?.expected_arrival) {
      setDelayError(
        "Expected arrival time is not available."
      );
      return;
    }

    setDelayLoading(true);
    setDelayError("");

    try {
      const response = await fetch(
        `${API_BASE}/journey/simulate-delay`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            expected_arrival: String(
              journey.expected_arrival
            ).replace("T", " "),
            exam_date: examDate,
            reporting_time: reportingTime,
            gate_closing_time: gateClosingTime,
            delay_minutes: minutes,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(getErrorMessage(data));
      }

      setDelayMinutes(minutes);
      setDelayResult(data);
    } catch (err) {
      if (err instanceof Error) {
        setDelayError(err.message);
      } else {
        setDelayError(
          "Unable to simulate journey delay."
        );
      }
    } finally {
      setDelayLoading(false);
    }
  }

  function captureGPS() {
    setGpsStatus("");
    setGpsLoading(true);

    if (!navigator.geolocation) {
      setGpsLoading(false);
      setGpsStatus(
        "GPS is not supported by this browser."
      );
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        setLastGps({ lat, lng });
        setCurrentLocation(
          `${lat.toFixed(5)}, ${lng.toFixed(5)}`
        );
        setGpsStatus(
          "GPS location captured successfully."
        );
        setGpsLoading(false);
      },
      () => {
        setGpsStatus(
          "Unable to access GPS. Please allow location permission."
        );
        setGpsLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 30000,
      }
    );
  }

  function openGoogleMaps() {
    const destination = encodeURIComponent(
      `${centreName}, ${centreAddress}, ${city}`
    );

    const origin = encodeURIComponent(
      currentLocation
    );

    window.open(
      `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}`,
      "_blank"
    );
  }

  function startJourney() {
    setStage("travel");
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  function markReached() {
    setStage("arrive");
    setShowPostArrival(true);
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  function openExamStatus() {
    setShowPostArrival(false);
    setShowExamComplete(true);
  }

  function completeExam(success: boolean) {
    setExamSuccessful(success);
    setShowExamComplete(false);
    setStage("exam");
  }

  function startReturnJourney() {
    setReturnJourney(true);
    setStage("home");
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  function resetAll() {
    setJourney(null);
    setCentre(null);
    setSupport(null);
    setError("");

    setDelayMinutes(0);
    setDelayResult(null);
    setDelayError("");

    setStage("plan");
    setShowPostArrival(false);
    setShowExamComplete(false);
    setExamSuccessful(null);
    setReturnJourney(false);
  }

  const risk = journey?.risk_level || "UNKNOWN";

  const timeline = Array.isArray(
    support?.exam_day_timeline
  )
    ? support.exam_day_timeline
    : [];

  const warnings = Array.isArray(
    support?.warnings
  )
    ? support.warnings
    : [];

  const checklist = Array.isArray(
    support?.preparation_checklist
  )
    ? support.preparation_checklist
    : [];

  const travelDuration = useMemo(
    () =>
      journey?.travel_duration_minutes ??
      journey?.total_travel_time ??
      journey?.estimated_travel_minutes,
    [journey]
  );

  const modeLabel = {
    car: "Car",
    bus: "Bus",
    train: "Train",
  }[travelMode];

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <div className="brand-icon">🎓</div>

            <div>
              <h1>Exam Journey Assistant</h1>
              <p>
                Plan your journey. Reduce uncertainty.
                Reach on time.
              </p>
            </div>
          </div>

          <div className="ai-badge">
            <span className="ai-dot"></span>
            AI-Powered Journey Planning
          </div>
        </div>
      </header>

      <main className="page">
        <section className="hero">
          <div className="hero-tag">
            SMART EXAM TRAVEL PLANNER
          </div>

          <h2>
            From <span>Home</span> to <span>Exam</span> and
            Back.
          </h2>

          <p>
            A complete journey assistant that helps
            examination candidates plan, monitor and
            complete their travel safely and on time.
          </p>

          {journey && (
            <div className="journey-progress">
              {[
                ["plan", "1", "Plan"],
                ["travel", "2", "Travel"],
                ["arrive", "3", "Arrive"],
                ["exam", "4", "Exam"],
                ["home", "5", "Home"],
              ].map(
                ([key, number, label]) => (
                  <div
                    className={`progress-step ${
                      stage === key ? "active" : ""
                    } ${
                      [
                        "travel",
                        "arrive",
                        "exam",
                        "home",
                      ].includes(stage) &&
                      key === "plan"
                        ? "done"
                        : ""
                    }`}
                    key={key}
                  >
                    <span>{number}</span>
                    <small>{label}</small>
                  </div>
                )
              )}
            </div>
          )}
        </section>

        {!journey && (
          <form
            className="card form-card"
            onSubmit={handleSubmit}
          >
            <div className="card-heading">
              <div className="heading-icon">👤</div>

              <div>
                <h3>Student &amp; Exam Details</h3>
                <p>
                  Provide the information required to create
                  your personalized journey plan.
                </p>
              </div>
            </div>

            <div className="form-grid">
              <div className="field">
                <label>Student Name</label>

                <input
                  value={name}
                  onChange={(e) =>
                    setName(e.target.value)
                  }
                  placeholder="Enter your name"
                  required
                />
              </div>

              <div className="field">
                <label>Exam Name</label>

                <input
                  value={examName}
                  onChange={(e) =>
                    setExamName(e.target.value)
                  }
                  placeholder="e.g. JEE, NEET, SSC"
                  required
                />
              </div>

              <div className="field">
                <label>Exam Date</label>

                <input
                  type="date"
                  value={examDate}
                  onChange={(e) =>
                    setExamDate(e.target.value)
                  }
                  required
                />
              </div>

              <div className="field">
                <label>Reporting Time</label>

                <input
                  type="time"
                  value={reportingTime}
                  onChange={(e) =>
                    setReportingTime(e.target.value)
                  }
                  required
                />
              </div>

              <div className="field">
                <label>Gate Closing Time</label>

                <input
                  type="time"
                  value={gateClosingTime}
                  onChange={(e) =>
                    setGateClosingTime(e.target.value)
                  }
                  required
                />
              </div>

              <div className="field">
                <label>Exam City</label>

                <input
                  value={city}
                  onChange={(e) =>
                    setCity(e.target.value)
                  }
                  placeholder="e.g. Gwalior"
                  required
                />
              </div>

              <div className="field">
                <label>Examination Centre</label>

                <input
                  value={centreName}
                  onChange={(e) =>
                    setCentreName(e.target.value)
                  }
                  placeholder="Enter centre name"
                  required
                />
              </div>

              <div className="field">
                <label>Centre Address</label>

                <input
                  value={centreAddress}
                  onChange={(e) =>
                    setCentreAddress(e.target.value)
                  }
                  placeholder="Enter complete centre address"
                  required
                />
              </div>

              <div className="field full">
                <label>Current Location</label>

                <div className="location-input">
                  <input
                    value={currentLocation}
                    onChange={(e) =>
                      setCurrentLocation(
                        e.target.value
                      )
                    }
                    placeholder="Enter starting location"
                    required
                  />

                  <button
                    type="button"
                    className="gps-button"
                    onClick={captureGPS}
                    disabled={gpsLoading}
                  >
                    📍{" "}
                    {gpsLoading
                      ? "Locating..."
                      : "Use GPS"}
                  </button>
                </div>

                {gpsStatus && (
                  <div className="gps-status">
                    {gpsStatus}
                  </div>
                )}
              </div>

              <div className="field full">
                <label>Travel Mode</label>

                <div className="mode-grid">
                  {[
                    ["car", "🚗", "Car"],
                    ["bus", "🚌", "Bus"],
                    ["train", "🚆", "Train"],
                  ].map(
                    ([value, icon, label]) => (
                      <button
                        type="button"
                        key={value}
                        className={`mode-card ${
                          travelMode === value
                            ? "selected"
                            : ""
                        }`}
                        onClick={() =>
                          setTravelMode(
                            value as TravelMode
                          )
                        }
                      >
                        <span>{icon}</span>
                        <strong>{label}</strong>

                        {travelMode === value && (
                          <small>Selected</small>
                        )}
                      </button>
                    )
                  )}
                </div>
              </div>
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="button button-primary"
                disabled={loading}
              >
                {loading
                  ? "Planning Journey..."
                  : "Plan My Journey →"}
              </button>
            </div>
          </form>
        )}

        {loading && (
          <div className="status loading-status">
            <div className="spinner"></div>

            <div>
              <strong>
                Analysing your journey...
              </strong>

              <span>
                Calculating route, arrival buffer and
                journey risk.
              </span>
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="status error-status">
            <div>⚠️</div>

            <div>
              <strong>
                Journey plan could not be generated
              </strong>

              <span>{error}</span>
            </div>
          </div>
        )}

        {journey && !loading && (
          <section className="dashboard">
            <div className="dashboard-header">
              <div>
                <span className="section-label">
                  JOURNEY ANALYSIS
                </span>

                <h2>Your Exam Journey Plan</h2>

                <p>
                  Prepared for <strong>{name}</strong> •{" "}
                  {examName}
                </p>
              </div>

              <div className="success-badge">
                ✓ Plan Generated
              </div>
            </div>

            <div
              className={`card risk-banner ${getRiskClass(
                risk
              )}`}
            >
              <div className="risk-left">
                <div className="risk-symbol">
                  {String(risk).toUpperCase() ===
                  "LOW"
                    ? "✓"
                    : "!"}
                </div>

                <div>
                  <span>
                    JOURNEY RISK LEVEL
                  </span>

                  <h3>
                    {String(risk).toUpperCase()}
                  </h3>

                  <p>
                    {support?.final_message ||
                      "Journey risk has been calculated from your travel plan."}
                  </p>
                </div>
              </div>

              <div className="risk-pill">
                {String(risk).toUpperCase()} RISK
              </div>
            </div>

            <div className="stat-grid">
              <div className="card stat-card">
                <div className="stat-icon">🚗</div>
                <span>Travel Mode</span>
                <strong>{modeLabel}</strong>
              </div>

              <div className="card stat-card">
                <div className="stat-icon">⏱️</div>
                <span>Travel Duration</span>

                <strong>
                  {formatMinutes(
                    travelDuration
                  )}
                </strong>
              </div>

              <div className="card stat-card">
                <div className="stat-icon">🛡️</div>
                <span>Available Buffer</span>

                <strong>
                  {formatMinutes(
                    journey.buffer_minutes ??
                      journey.available_buffer
                  )}
                </strong>
              </div>

              <div className="card stat-card">
                <div className="stat-icon">📍</div>
                <span>Expected Arrival</span>

                <strong>
                  {formatDateTime(
                    journey.expected_arrival
                  )}
                </strong>
              </div>
            </div>

            {/* =====================================================
                DELAY SIMULATION
            ====================================================== */}

            <div
              className="card"
              style={{
                marginTop: "20px",
                padding: "24px",
              }}
            >
              <div className="panel-heading">
                <div className="panel-icon">⚠️</div>

                <div>
                  <h3>
                    Journey Delay Simulation
                  </h3>

                  <p>
                    Simulate unexpected traffic,
                    transport or route delays and see
                    how the journey risk changes.
                  </p>
                </div>
              </div>

              <div
                style={{
                  marginTop: "18px",
                  padding: "16px",
                  borderRadius: "12px",
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                }}
              >
                <strong>
                  Simulate a transportation delay
                </strong>

                <p
                  style={{
                    margin: "6px 0 16px",
                    color: "#64748b",
                  }}
                >
                  This demonstrates how the assistant
                  reacts when real-world travel does not
                  go according to plan.
                </p>

                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "10px",
                  }}
                >
                  {[15, 30, 45, 60, 75, 90].map(
                    (minutes) => (
                      <button
                        key={minutes}
                        type="button"
                        className="button button-secondary"
                        onClick={() =>
                          simulateDelay(minutes)
                        }
                        disabled={delayLoading}
                      >
                        +{minutes} min
                      </button>
                    )
                  )}

                  <button
                    type="button"
                    className="button button-primary"
                    onClick={() =>
                      simulateDelay(0)
                    }
                    disabled={delayLoading}
                  >
                    Reset
                  </button>
                </div>

                {delayLoading && (
                  <div
                    style={{
                      marginTop: "16px",
                      fontWeight: 600,
                    }}
                  >
                    🔄 Recalculating journey risk...
                  </div>
                )}

                {delayError && (
                  <div
                    style={{
                      marginTop: "16px",
                      padding: "12px",
                      borderRadius: "8px",
                      background: "#fee2e2",
                      color: "#991b1b",
                    }}
                  >
                    ⚠️ {delayError}
                  </div>
                )}

                {delayResult &&
                  !delayLoading && (
                    <div
                      style={{
                        marginTop: "20px",
                        padding: "18px",
                        borderRadius: "12px",
                        border:
                          "1px solid #cbd5e1",
                        background: "#ffffff",
                      }}
                    >
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "repeat(auto-fit, minmax(160px, 1fr))",
                          gap: "14px",
                        }}
                      >
                        <div>
                          <small>DELAY</small>

                          <strong
                            style={{
                              display: "block",
                              marginTop: "4px",
                            }}
                          >
                            +
                            {
                              delayResult.delay_minutes
                            }{" "}
                            min
                          </strong>
                        </div>

                        <div>
                          <small>
                            NEW EXPECTED ARRIVAL
                          </small>

                          <strong
                            style={{
                              display: "block",
                              marginTop: "4px",
                            }}
                          >
                            {formatDateTime(
                              delayResult.new_expected_arrival
                            )}
                          </strong>
                        </div>

                        <div>
                          <small>
                            REMAINING BUFFER
                          </small>

                          <strong
                            style={{
                              display: "block",
                              marginTop: "4px",
                            }}
                          >
                            {formatMinutes(
                              delayResult.buffer_minutes
                            )}
                          </strong>
                        </div>

                        <div>
                          <small>
                            UPDATED RISK
                          </small>

                          <strong
                            className={getRiskClass(
                              delayResult.risk_level
                            )}
                            style={{
                              display: "block",
                              marginTop: "4px",
                            }}
                          >
                            {String(
                              delayResult.risk_level
                            ).toUpperCase()}
                          </strong>
                        </div>
                      </div>

                      <div
                        style={{
                          marginTop: "16px",
                          padding: "14px",
                          borderRadius: "8px",
                          background: "#f1f5f9",
                        }}
                      >
                        <strong>
                          Assistant Recommendation
                        </strong>

                        <p
                          style={{
                            marginBottom: 0,
                          }}
                        >
                          {formatValue(
                            delayResult.recommendation
                          )}
                        </p>
                      </div>
                    </div>
                  )}

                {delayMinutes > 0 &&
                  delayResult && (
                    <div
                      style={{
                        marginTop: "14px",
                        fontSize: "13px",
                        color: "#64748b",
                      }}
                    >
                      Simulation active: +
                      {delayMinutes} minute
                      transportation delay.
                    </div>
                  )}
              </div>
            </div>

            {/* =====================================================
                LIVE JOURNEY
            ====================================================== */}

            <div className="live-card">
              <div className="live-top">
                <div>
                  <span className="section-label">
                    LIVE JOURNEY
                  </span>

                  <h3>
                    Your journey is ready to monitor
                  </h3>
                </div>

                <span className="live-badge">
                  <i></i> LIVE READY
                </span>
              </div>

              <div className="route-visual">
                <div className="route-point">
                  <span className="route-dot start"></span>

                  <div>
                    <small>
                      STARTING POINT
                    </small>

                    <strong>
                      {currentLocation}
                    </strong>
                  </div>
                </div>

                <div className="route-line">
                  <span>↓</span>
                  <small>{modeLabel}</small>
                </div>

                <div className="route-point">
                  <span className="route-dot destination"></span>

                  <div>
                    <small>
                      DESTINATION
                    </small>

                    <strong>
                      {centreName}, {city}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="live-actions">
                <button
                  className="button button-primary"
                  onClick={startJourney}
                >
                  🚀 Start Journey
                </button>

                <button
                  className="button button-secondary"
                  onClick={openGoogleMaps}
                >
                  🗺️ Open Google Maps
                </button>
              </div>
            </div>

            <div className="content-grid">
              <div className="card panel">
                <div className="panel-heading">
                  <div className="panel-icon">🧭</div>

                  <div>
                    <h3>Journey Summary</h3>
                    <p>
                      Your planned route and
                      examination schedule
                    </p>
                  </div>
                </div>

                <div className="details">
                  <div className="detail">
                    <span>Starting Point</span>
                    <strong>
                      {currentLocation}
                    </strong>
                  </div>

                  <div className="detail">
                    <span>Travel Mode</span>
                    <strong>{modeLabel}</strong>
                  </div>

                  <div className="detail">
                    <span>Exam Centre</span>

                    <strong>
                      {formatValue(
                        journey.exam_centre ??
                          centre?.centre_name ??
                          centreName
                      )}
                    </strong>
                  </div>

                  <div className="detail">
                    <span>Exam Date</span>

                    <strong>
                      {formatValue(
                        journey.exam_date ??
                          centre?.exam_date ??
                          examDate
                      )}
                    </strong>
                  </div>

                  <div className="detail">
                    <span>Reporting Time</span>

                    <strong>
                      {formatValue(
                        centre?.reporting_time ??
                          reportingTime
                      )}
                    </strong>
                  </div>

                  <div className="detail">
                    <span>Gate Closing</span>

                    <strong>
                      {formatValue(
                        centre?.gate_closing_time ??
                          gateClosingTime
                      )}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="card panel">
                <div className="panel-heading">
                  <div className="panel-icon">📍</div>

                  <div>
                    <h3>
                      Centre Information
                    </h3>

                    <p>
                      Important examination centre
                      details
                    </p>
                  </div>
                </div>

                <div className="details">
                  <div className="detail">
                    <span>Centre</span>
                    <strong>
                      {centreName}
                    </strong>
                  </div>

                  <div className="detail">
                    <span>Address</span>
                    <strong>
                      {centreAddress}
                    </strong>
                  </div>

                  <div className="detail">
                    <span>City</span>
                    <strong>{city}</strong>
                  </div>

                  <div className="detail">
                    <span>
                      Recommended Arrival
                    </span>

                    <strong className="highlight">
                      {formatValue(
                        support?.recommended_arrival_time
                      )}
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="ai-panel">
              <div className="ai-panel-icon">
                🤖
              </div>

              <div>
                <span>
                  SMART JOURNEY INTELLIGENCE
                </span>

                <h3>AI Recommendation</h3>

                <p>
                  {String(risk).toUpperCase() ===
                  "LOW"
                    ? "Your current journey has a comfortable safety buffer. The planned route is suitable for the examination schedule."
                    : "Your journey requires additional attention. Consider leaving earlier and keeping a reliable backup option ready."}
                </p>

                <div className="ai-checks">
                  <span>✓ Travel time</span>
                  <span>✓ Reporting time</span>
                  <span>✓ Safety buffer</span>
                  <span>✓ Journey risk</span>
                </div>
              </div>
            </div>

            <div className="journey-monitor card">
              <div className="panel-heading">
                <div className="panel-icon">📡</div>

                <div>
                  <h3>
                    Live Journey Monitoring
                  </h3>

                  <p>
                    Monitor your current journey
                    position
                  </p>
                </div>

                <span className="live-badge">
                  <i></i> LIVE
                </span>
              </div>

              <div className="monitor-grid">
                <div>
                  <small>
                    CURRENT LOCATION
                  </small>

                  <strong>
                    {lastGps
                      ? `${lastGps.lat.toFixed(
                          5
                        )}, ${lastGps.lng.toFixed(5)}`
                      : currentLocation}
                  </strong>
                </div>

                <div>
                  <small>DESTINATION</small>

                  <strong>
                    {centreName}, {city}
                  </strong>
                </div>

                <div>
                  <small>TRAVEL MODE</small>

                  <strong>{modeLabel}</strong>
                </div>
              </div>

              <div className="monitor-actions">
                <button
                  className="button button-secondary"
                  onClick={captureGPS}
                >
                  📍 Refresh GPS
                </button>

                <button
                  className="button button-secondary"
                  onClick={openGoogleMaps}
                >
                  🗺️ View Navigation
                </button>

                <button
                  className="button button-success"
                  onClick={markReached}
                >
                  ✓ I Have Reached
                </button>
              </div>
            </div>

            {stage === "travel" && (
              <div className="journey-alert">
                <span>📡</span>

                <div>
                  <strong>
                    Journey monitoring active
                  </strong>

                  <p>
                    Your journey is now in travel mode.
                    Keep location access enabled and
                    follow the navigation route.
                  </p>
                </div>
              </div>
            )}

            {showPostArrival && (
              <div className="arrival-card">
                <div className="arrival-icon">
                  🎉
                </div>

                <span className="section-label">
                  DESTINATION REACHED
                </span>

                <h2>Journey Successful</h2>

                <p>
                  You have reached the examination area.
                  What would you like to do next?
                </p>

                <div className="service-grid">
                  <button className="service-card">
                    <span>🏨</span>
                    <strong>Find Stay</strong>
                    <small>
                      Hotels & accommodation
                    </small>
                  </button>

                  <button className="service-card">
                    <span>🍽️</span>
                    <strong>
                      Food & Breakfast
                    </strong>
                    <small>
                      Nearby food options
                    </small>
                  </button>

                  <button className="service-card">
                    <span>🚕</span>
                    <strong>Local Cab</strong>
                    <small>
                      Reach nearby locations
                    </small>
                  </button>

                  <button
                    className="service-card primary-service"
                    onClick={openExamStatus}
                  >
                    <span>📝</span>
                    <strong>
                      Continue to Exam
                    </strong>
                    <small>
                      Mark your exam status
                    </small>
                  </button>
                </div>

                <div className="prototype-label">
                  Prototype services are designed for
                  future authorized hotel, food and
                  mobility integrations.
                </div>
              </div>
            )}

            {showExamComplete && (
              <div className="modal-backdrop">
                <div className="modal-card">
                  <div className="modal-icon">
                    📝
                  </div>

                  <span className="section-label">
                    EXAM STATUS
                  </span>

                  <h2>
                    How did your examination go?
                  </h2>

                  <p>
                    Your response helps us complete
                    your journey and prepare your
                    return trip.
                  </p>

                  <div className="exam-buttons">
                    <button
                      className="button button-success"
                      onClick={() =>
                        completeExam(true)
                      }
                    >
                      ✓ Exam Successful
                    </button>

                    <button
                      className="button button-secondary"
                      onClick={() =>
                        completeExam(false)
                      }
                    >
                      Submit Feedback
                    </button>
                  </div>
                </div>
              </div>
            )}

            {stage === "exam" && (
              <div className="exam-result">
                <div className="exam-result-icon">
                  {examSuccessful ? "🎉" : "💬"}
                </div>

                <span className="section-label">
                  EXAM COMPLETED
                </span>

                <h2>
                  {examSuccessful
                    ? "Exam marked successfully!"
                    : "Thank you for your feedback."}
                </h2>

                <p>
                  {examSuccessful
                    ? "Your exam journey is now ready for the return-home phase."
                    : "Your feedback has been recorded in this prototype flow."}
                </p>

                <button
                  className="button button-primary"
                  onClick={startReturnJourney}
                >
                  🏠 Yes, Plan My Return Journey →
                </button>
              </div>
            )}

            {stage === "home" &&
              returnJourney && (
                <div className="return-card">
                  <div className="return-header">
                    <div>
                      <span className="section-label">
                        RETURN JOURNEY
                      </span>

                      <h2>
                        Plan Your Journey Home
                      </h2>

                      <p>
                        Your exam is complete. We can
                        now help you plan the journey
                        back home.
                      </p>
                    </div>

                    <div className="home-icon">
                      🏠
                    </div>
                  </div>

                  <div className="return-route">
                    <div>
                      <small>FROM</small>
                      <strong>{city}</strong>
                    </div>

                    <span>→</span>

                    <div>
                      <small>TO</small>

                      <strong>
                        {currentLocation}
                      </strong>
                    </div>
                  </div>

                  <div className="return-options">
                    <div className="return-option">
                      <span>🚆</span>

                      <div>
                        <strong>Train</strong>

                        <small>
                          Check available return
                          connections
                        </small>
                      </div>
                    </div>

                    <div className="return-option">
                      <span>🚌</span>

                      <div>
                        <strong>Bus</strong>

                        <small>
                          Explore return bus
                          options
                        </small>
                      </div>
                    </div>

                    <div className="return-option">
                      <span>🚕</span>

                      <div>
                        <strong>Local Cab</strong>

                        <small>
                          Reach station or bus stand
                        </small>
                      </div>
                    </div>
                  </div>

                  <div className="parent-status">
                    <div className="parent-status-icon">
                      👨‍👩‍👦
                    </div>

                    <div>
                      <strong>
                        Parent Journey Updates
                      </strong>

                      <p>
                        Future version can securely
                        share important journey
                        milestones such as departure,
                        arrival and exam completion
                        with authorized contacts.
                      </p>
                    </div>

                    <span className="planned-badge">
                      PLANNED
                    </span>
                  </div>

                  <button
                    className="button button-primary"
                    onClick={() =>
                      alert(
                        "Return journey planning module is ready for integration."
                      )
                    }
                  >
                    🚀 Start Return Planning
                  </button>
                </div>
              )}

            <div className="content-grid">
              <div className="card panel">
                <div className="panel-heading">
                  <div className="panel-icon">
                    💡
                  </div>

                  <div>
                    <h3>
                      Recommendation
                    </h3>

                    <p>
                      What you should do before
                      travelling
                    </p>
                  </div>
                </div>

                <div className="recommendation">
                  <div>✓</div>

                  <p>
                    {formatValue(
                      support?.final_message ||
                        "Keep sufficient travel buffer and follow the planned route."
                    )}
                  </p>
                </div>

                {support?.delay_action && (
                  <div className="action-box">
                    <strong>
                      If a delay occurs
                    </strong>

                    <p>
                      {formatValue(
                        support.delay_action
                      )}
                    </p>
                  </div>
                )}

                {support?.backup_guidance && (
                  <div className="action-box">
                    <strong>
                      Backup guidance
                    </strong>

                    <p>
                      {formatValue(
                        support.backup_guidance
                      )}
                    </p>
                  </div>
                )}
              </div>

              <div className="card panel">
                <div className="panel-heading">
                  <div className="panel-icon">
                    ⚠️
                  </div>

                  <div>
                    <h3>Warnings</h3>

                    <p>
                      Things you should keep in mind
                    </p>
                  </div>
                </div>

                <div className="warning-list">
                  {warnings.length > 0 ? (
                    warnings.map(
                      (
                        warning: any,
                        index: number
                      ) => (
                        <div
                          className="warning-item"
                          key={index}
                        >
                          <span>!</span>

                          <p>
                            {formatValue(
                              warning
                            )}
                          </p>
                        </div>
                      )
                    )
                  ) : (
                    <div className="empty-state">
                      No additional warnings.
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="content-grid">
              <div className="card panel">
                <div className="panel-heading">
                  <div className="panel-icon">
                    📝
                  </div>

                  <div>
                    <h3>
                      Exam-Day Checklist
                    </h3>

                    <p>
                      Prepare these items before
                      leaving
                    </p>
                  </div>
                </div>

                <div className="checklist">
                  {checklist.map(
                    (
                      item: any,
                      index: number
                    ) => (
                      <div
                        className="check-item"
                        key={index}
                      >
                        <div className="check-box">
                          ✓
                        </div>

                        <span>
                          {formatValue(item)}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>

              <div className="card panel">
                <div className="panel-heading">
                  <div className="panel-icon">
                    🕐
                  </div>

                  <div>
                    <h3>
                      Journey Timeline
                    </h3>

                    <p>
                      Important events for your
                      exam journey
                    </p>
                  </div>
                </div>

                <div className="timeline">
                  {timeline.length > 0 ? (
                    timeline.map(
                      (
                        item: any,
                        index: number
                      ) => (
                        <div
                          className="timeline-item"
                          key={index}
                        >
                          <div className="timeline-dot">
                            {index + 1}
                          </div>

                          <strong>
                            {formatValue(item)}
                          </strong>
                        </div>
                      )
                    )
                  ) : (
                    <>
                      <div className="timeline-item">
                        <div className="timeline-dot">
                          1
                        </div>

                        <strong>
                          {formatDateTime(
                            journey.departure_time
                          )}{" "}
                          - Planned departure
                        </strong>
                      </div>

                      <div className="timeline-item">
                        <div className="timeline-dot">
                          2
                        </div>

                        <strong>
                          {formatDateTime(
                            journey.expected_arrival
                          )}{" "}
                          - Expected arrival
                        </strong>
                      </div>

                      <div className="timeline-item">
                        <div className="timeline-dot">
                          3
                        </div>

                        <strong>
                          {examDate}{" "}
                          {reportingTime} -
                          Official reporting
                        </strong>
                      </div>

                      <div className="timeline-item">
                        <div className="timeline-dot">
                          4
                        </div>

                        <strong>
                          {examDate}{" "}
                          {gateClosingTime} -
                          Gate closing
                        </strong>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="future-features">
              <div>
                <span>🚆</span>

                <strong>
                  Railway Intelligence
                </strong>

                <small>
                  Train number, live running status
                  and ETA via authorized railway
                  data services.
                </small>
              </div>

              <div>
                <span>🏨</span>

                <strong>Stay & Food</strong>

                <small>
                  Accommodation and food discovery
                  around the destination.
                </small>
              </div>

              <div>
                <span>👨‍👩‍👦</span>

                <strong>Family Updates</strong>

                <small>
                  Secure milestone notifications
                  for authorized contacts.
                </small>
              </div>
            </div>

            <div className="prototype-note">
              <span>ℹ️</span>

              <p>
                This SIH prototype demonstrates the
                complete student journey experience.
                Google Maps navigation and browser GPS
                are available now. Railway live status,
                hotel, food, cab booking and family
                notifications require their respective
                authorized APIs and production services.
              </p>
            </div>

            <button
              className="reset-link"
              onClick={resetAll}
            >
              ← Create another journey
            </button>
          </section>
        )}
      </main>

      <footer className="footer">
        <p>
          Exam Journey Assistant • Smart Travel
          Planning for Examination Candidates
        </p>
      </footer>
    </div>
  );
}

export default App;

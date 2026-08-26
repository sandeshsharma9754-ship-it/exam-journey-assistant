import { useState } from "react";
import "./App.css";

function App() {
  const [form, setForm] = useState({
    starting_location: "",
    exam_centre: "",
    exam_date: "",
    reporting_time: "",
    gate_closing_time: "",
    local_travel_minutes: 0,
    transport_delay_minutes: 0,
    departure_time: "",
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]:
        name === "local_travel_minutes" ||
        name === "transport_delay_minutes"
          ? Number(value)
          : value,
    }));
  };

  const generatePlan = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/exam/complete-plan",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...form,
            departure_time: form.departure_time || null,
            centre_name: form.exam_centre,
            centre_address: form.exam_centre,
            centre_city: form.exam_centre,
            centre_latitude: null,
            centre_longitude: null,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to generate journey plan"
        );
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Exam Journey Assistant</h1>
          <p>
            Plan your examination journey with confidence.
          </p>
        </div>
      </header>

      <main className="container">

        {/* INPUT FORM */}
        <section className="card">
          <h2>Plan Your Exam Journey</h2>

          <p className="subtitle">
            Enter your examination and travel details.
          </p>

          <div className="form-grid">

            <div className="field">
              <label>Starting Location</label>

              <input
                name="starting_location"
                placeholder="e.g. Bhopal, Madhya Pradesh"
                value={form.starting_location}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>Exam Centre</label>

              <input
                name="exam_centre"
                placeholder="e.g. Indore, Madhya Pradesh"
                value={form.exam_centre}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>Exam Date</label>

              <input
                type="date"
                name="exam_date"
                value={form.exam_date}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>Reporting Time</label>

              <input
                type="time"
                name="reporting_time"
                value={form.reporting_time}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>Gate Closing Time</label>

              <input
                type="time"
                name="gate_closing_time"
                value={form.gate_closing_time}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>Local Travel (minutes)</label>

              <input
                type="number"
                name="local_travel_minutes"
                min="0"
                value={form.local_travel_minutes}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>Expected Transport Delay (minutes)</label>

              <input
                type="number"
                name="transport_delay_minutes"
                min="0"
                value={form.transport_delay_minutes}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>Departure Time</label>

              <input
                type="datetime-local"
                name="departure_time"
                value={form.departure_time}
                onChange={handleChange}
              />
            </div>

          </div>

          <button
            className="generate-btn"
            onClick={generatePlan}
            disabled={loading}
          >
            {loading
              ? "Generating Journey Plan..."
              : "Generate Journey Plan"}
          </button>

          {error && (
            <div className="error">
              {error}
            </div>
          )}
        </section>


        {/* RESULTS */}
        {result && result.exam_plan && (
          <section className="results">

            {/* JOURNEY OVERVIEW */}
            <div className="card">
              <h2>Journey Overview</h2>

              <div className="stats">

                <div className="stat">
                  <span>Departure</span>

                  <strong>
                    {result.exam_plan.journey.departure_time}
                  </strong>
                </div>

                <div className="stat">
                  <span>Expected Arrival</span>

                  <strong>
                    {result.exam_plan.journey.expected_arrival}
                  </strong>
                </div>

                <div className="stat">
                  <span>Total Travel</span>

                  <strong>
                    {result.exam_plan.journey.total_travel_minutes} min
                  </strong>
                </div>

                <div className="stat">
                  <span>Buffer</span>

                  <strong>
                    {result.exam_plan.journey.buffer_minutes} min
                  </strong>
                </div>

              </div>

              <div className="risk">
                Risk Level:{" "}
                <strong>
                  {result.exam_plan.journey.risk_level}
                </strong>
              </div>

              <p className="recommendation">
                {result.exam_plan.journey.recommendation}
              </p>
            </div>


            {/* EXAM CENTRE */}
            <div className="card">
              <h2>Exam Centre Information</h2>

              <p>
                <strong>Centre:</strong>{" "}
                {result.exam_plan.centre.centre_name}
              </p>

              <p>
                <strong>Address:</strong>{" "}
                {result.exam_plan.centre.address}
              </p>

              <p>
                <strong>City:</strong>{" "}
                {result.exam_plan.centre.city}
              </p>

              <p>
                <strong>Exam Date:</strong>{" "}
                {result.exam_plan.centre.exam_date}
              </p>

              <p>
                <strong>Reporting Time:</strong>{" "}
                {result.exam_plan.centre.reporting_time}
              </p>

              <p>
                <strong>Gate Closing Time:</strong>{" "}
                {result.exam_plan.centre.gate_closing_time}
              </p>

              <p>
                <strong>Recommended Arrival:</strong>{" "}
                {result.exam_plan.student_support.recommended_arrival_time}
              </p>

              <h3>Preparation Checklist</h3>

              <ul>
                {result.exam_plan.student_support.preparation_checklist.map(
                  (item: string, index: number) => (
                    <li key={index}>{item}</li>
                  )
                )}
              </ul>

              <h3>Warnings</h3>

              <ul>
                {result.exam_plan.student_support.warnings.map(
                  (item: string, index: number) => (
                    <li key={index}>{item}</li>
                  )
                )}
              </ul>
            </div>


            {/* EXAM DAY TIMELINE */}
            <div className="card">
              <h2>Exam Day Timeline</h2>

              <div className="timeline">
                {result.exam_plan.student_support.exam_day_timeline.map(
                  (item: string, index: number) => (
                    <div
                      className="timeline-item"
                      key={index}
                    >
                      {item}
                    </div>
                  )
                )}
              </div>

              <h3>Delay Action</h3>

              <p>
                {result.exam_plan.student_support.delay_action}
              </p>

              <h3>Final Guidance</h3>

              <p>
                {result.exam_plan.student_support.final_message}
              </p>

              <p>
                <strong>Backup:</strong>{" "}
                {result.exam_plan.student_support.backup_guidance}
              </p>
            </div>

          </section>
        )}

      </main>
    </div>
  );
}

export default App;
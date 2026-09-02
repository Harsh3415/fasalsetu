import { useState } from "react";

function App() {

  const [result, setResult] = useState(null);

  const submitClaim = async (e) => {
    e.preventDefault();

    const form = new FormData(e.target);

    const response = await fetch(
      "http://localhost:8000/assess",
      {
        method: "POST",
        body: form
      }
    );

    const data = await response.json();

    setResult(data);
  };

  return (
    <div style={{
      maxWidth: "900px",
      margin: "auto",
      padding: "40px",
      fontFamily: "Arial"
    }}>

      <h1>🌾 FasalSetu</h1>

      <p>
        AI-Powered Rapid Crop-Loss Assessment
        & Claim Triage
      </p>

      <form onSubmit={submitClaim}>

        <label>Crop</label>
        <br />

        <select name="crop">
          <option>Wheat</option>
          <option>Rice</option>
          <option>Maize</option>
          <option>Cotton</option>
        </select>

        <br /><br />

        <label>Damage Type</label>
        <br />

        <select name="damage_type">
          <option>Flood Submergence</option>
          <option>Drought</option>
          <option>Storm</option>
          <option>Pest Attack</option>
        </select>

        <br /><br />

        <label>Area (hectares)</label>
        <br />

        <input
          name="area"
          type="number"
          step="0.1"
          defaultValue="2.3"
        />

        <br /><br />

        <label>Latitude</label>
        <br />

        <input
          name="latitude"
          defaultValue="28.6139"
        />

        <br /><br />

        <label>Longitude</label>
        <br />

        <input
          name="longitude"
          defaultValue="77.2090"
        />

        <br /><br />

        <label>Upload Field Image</label>
        <br />

        <input
          name="image"
          type="file"
          accept="image/*"
          required
        />

        <br /><br />

        <button type="submit">
          Assess Crop Damage
        </button>

      </form>

      {result && (

        <div style={{
          marginTop: "40px",
          padding: "25px",
          border: "1px solid #ddd",
          borderRadius: "15px"
        }}>

          <h2>AI Assessment</h2>

          <p>
            <b>Field ID:</b> {result.field_id}
          </p>

          <p>
            <b>Crop:</b> {result.crop}
          </p>

          <p>
            <b>Damage:</b> {result.damage_percentage}%
          </p>

          <p>
            <b>Evidence Confidence:</b> {result.confidence}%
          </p>

          <p>
            <b>Consistency Score:</b>
            {" "}
            {result.consistency_score}%
          </p>

          <h3>
            Priority: {result.priority}
          </h3>

          <p>
            {result.recommendation}
          </p>

          <hr />

          <p>
            👨‍🌾 Human surveyor makes the final decision.
          </p>

        </div>

      )}

    </div>
  );
}

export default App;
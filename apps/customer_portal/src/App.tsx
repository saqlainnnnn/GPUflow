import { FormEvent, useEffect, useState } from "react";
import "./App.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";

const CUSTOMER_ID =
  import.meta.env.VITE_CUSTOMER_ID ?? "";

type Customer = {
  id: string;
  external_id: string;
  company_name: string;
  email: string;
  country: string;
  status: string;
};

type Allocation = {
  id: string;
  customer_id: string;
  gpu_type: string;
  gpu_count: number;
  region: string;
  status: string;
};

type Job = {
  id: string;
  external_id: string;
  customer_id: string;
  allocation_id: string;
  gpu_type: string;
  gpu_count: number;
  status: string;
  duration_seconds: number;
  failure_reason: string | null;
};

type UsageSummary = {
  customer_id: string;
  total_gpu_hours: number;
  average_utilization: number;
  event_count: number;
  gpu_hours_7d: number;
  gpu_hours_30d: number;
  growth_7d_percent: number | null;
  growth_30d_percent: number | null;
};

type GPUTypeUsage = {
  gpu_type: string;
  gpu_hours: number;
  average_utilization: number;
};

type DailyUsage = {
  date: string;
  gpu_hours: number;
  average_utilization: number;
};

type CustomerSummary = {
  customer: Customer;
  allocations: Allocation[];
  jobs: Job[];
  usage: {
    customer_id: string;
    summary: UsageSummary;
    by_gpu_type: GPUTypeUsage[];
    daily: DailyUsage[];
  };
};

function App() {
  const [data, setData] = useState<CustomerSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const [gpuType, setGpuType] = useState("A100");
  const [gpuCount, setGpuCount] = useState(1);
  const [region, setRegion] = useState("us-east");

  const [jobExternalId, setJobExternalId] = useState("");
  const [jobAllocationId, setJobAllocationId] = useState("");
  const [jobGpuCount, setJobGpuCount] = useState(1);

  const loadDashboard = async () => {
    if (!CUSTOMER_ID) {
      throw new Error("VITE_CUSTOMER_ID is not configured");
    }

    const response = await fetch(
      `${API_BASE}/api/v1/customers/${CUSTOMER_ID}/summary`,
    );

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    return (await response.json()) as CustomerSummary;
  };

  useEffect(() => {
    loadDashboard()
      .then(setData)
      .catch((err: Error) => {
        setError(err.message);
      });
  }, []);

  const handleCreateAllocation = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setActionMessage(null);

    const response = await fetch(
      `${API_BASE}/api/v1/allocations`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          customer_id: CUSTOMER_ID,
          gpu_type: gpuType,
          gpu_count: gpuCount,
          region,
        }),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      setActionMessage(
        body.detail ?? `Allocation failed (${response.status})`,
      );
      return;
    }

    setActionMessage("GPU allocation created.");
    setGpuCount(1);

    const refreshed = await loadDashboard();
    setData(refreshed);
    setJobAllocationId(body.id);
  };

  const handleCreateJob = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setActionMessage(null);

    const response = await fetch(
      `${API_BASE}/api/v1/jobs`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          external_id: jobExternalId,
          customer_id: CUSTOMER_ID,
          allocation_id: jobAllocationId,
          gpu_count: jobGpuCount,
          status: "pending",
        }),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      setActionMessage(
        body.detail ?? `Job creation failed (${response.status})`,
      );
      return;
    }

    setActionMessage("GPU job created.");
    setJobExternalId("");

    const refreshed = await loadDashboard();
    setData(refreshed);
  };

  if (error) {
    return (
      <main className="page">
        <div className="error-card">
          <h1>Unable to load dashboard</h1>
          <p>{error}</p>
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="page">
        <div className="loading">Loading dashboard...</div>
      </main>
    );
  }

  const { customer, allocations, jobs, usage } = data;
  const summary = usage.summary;

  return (
    <main className="page">
      <header className="header">
        <div>
          <p className="eyebrow">GPUFlow</p>
          <h1>{customer.company_name}</h1>
          <p className="muted">
            {customer.email} · {customer.country}
          </p>
        </div>

        <span className={`status ${customer.status}`}>
          {customer.status}
        </span>
      </header>

      {actionMessage && (
        <div className="notice">
          {actionMessage}
        </div>
      )}

      <section className="metrics">
        <Metric
          label="Total GPU hours"
          value={summary.total_gpu_hours.toFixed(2)}
        />
        <Metric
          label="7d GPU hours"
          value={summary.gpu_hours_7d.toFixed(2)}
        />
        <Metric
          label="30d GPU hours"
          value={summary.gpu_hours_30d.toFixed(2)}
        />
        <Metric
          label="Avg utilization"
          value={`${(
            summary.average_utilization * 100
          ).toFixed(1)}%`}
        />
      </section>

      <section className="grid">
        <div className="card">
          <div className="card-header">
            <div>
              <h2>Request allocation</h2>
              <p className="muted">
                Reserve GPU capacity
              </p>
            </div>
          </div>

          <form className="form" onSubmit={handleCreateAllocation}>
            <label>
              GPU type
              <input
                value={gpuType}
                onChange={(e) => setGpuType(e.target.value)}
                placeholder="A100"
                required
              />
            </label>

            <label>
              GPU count
              <input
                type="number"
                min={1}
                value={gpuCount}
                onChange={(e) =>
                  setGpuCount(Number(e.target.value))
                }
                required
              />
            </label>

            <label>
              Region
              <input
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                placeholder="us-east"
                required
              />
            </label>

            <button type="submit">
              Request allocation
            </button>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h2>Launch job</h2>
              <p className="muted">
                Run compute on an allocation
              </p>
            </div>
          </div>

          <form className="form" onSubmit={handleCreateJob}>
            <label>
              Job external ID
              <input
                value={jobExternalId}
                onChange={(e) =>
                  setJobExternalId(e.target.value)
                }
                placeholder="training-run-001"
                required
              />
            </label>

            <label>
              Allocation
              <select
                value={jobAllocationId}
                onChange={(e) =>
                  setJobAllocationId(e.target.value)
                }
                required
              >
                <option value="" disabled>
                  Select allocation
                </option>

                {allocations
                  .filter(
                    (allocation) =>
                      allocation.status === "active",
                  )
                  .map((allocation) => (
                    <option
                      key={allocation.id}
                      value={allocation.id}
                    >
                      {allocation.gpu_type} ·{" "}
                      {allocation.gpu_count} GPU ·{" "}
                      {allocation.region}
                    </option>
                  ))}
              </select>
            </label>

            <label>
              GPU count
              <input
                type="number"
                min={1}
                value={jobGpuCount}
                onChange={(e) =>
                  setJobGpuCount(Number(e.target.value))
                }
                required
              />
            </label>

            <button
              type="submit"
              disabled={allocations.length === 0}
            >
              Create job
            </button>
          </form>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <div className="card-header">
            <div>
              <h2>Usage trend</h2>
              <p className="muted">
                Daily GPU hours
              </p>
            </div>
          </div>

          {usage.daily.length === 0 ? (
            <EmptyState text="No usage data yet." />
          ) : (
            <div className="bars">
              {usage.daily.map((day) => {
                const max = Math.max(
                  ...usage.daily.map(
                    (item) => item.gpu_hours,
                  ),
                  1,
                );

                return (
                  <div className="bar-column" key={day.date}>
                    <div className="bar-value">
                      {day.gpu_hours.toFixed(1)}
                    </div>
                    <div
                      className="bar"
                      style={{
                        height: `${Math.max(
                          (day.gpu_hours / max) * 180,
                          4,
                        )}px`,
                      }}
                    />
                    <span>{day.date.slice(5)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h2>GPU types</h2>
              <p className="muted">
                Usage by accelerator
              </p>
            </div>
          </div>

          {usage.by_gpu_type.length === 0 ? (
            <EmptyState text="No GPU usage yet." />
          ) : (
            <div className="list">
              {usage.by_gpu_type.map((item) => (
                <div className="list-row" key={item.gpu_type}>
                  <div>
                    <strong>{item.gpu_type}</strong>
                    <span className="muted">
                      {(
                        item.average_utilization * 100
                      ).toFixed(1)}
                      % utilization
                    </span>
                  </div>

                  <strong>
                    {item.gpu_hours.toFixed(2)}h
                  </strong>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <div className="card-header">
            <div>
              <h2>Allocations</h2>
              <p className="muted">
                Current GPU capacity
              </p>
            </div>

            <span className="count">
              {allocations.length}
            </span>
          </div>

          {allocations.length === 0 ? (
            <EmptyState text="No allocations yet." />
          ) : (
            <div className="list">
              {allocations.map((allocation) => (
                <div
                  className="list-row"
                  key={allocation.id}
                >
                  <div>
                    <strong>{allocation.gpu_type}</strong>
                    <span className="muted">
                      {allocation.region}
                    </span>
                  </div>

                  <div className="right">
                    <strong>
                      {allocation.gpu_count} GPU
                      {allocation.gpu_count === 1
                        ? ""
                        : "s"}
                    </strong>
                    <span className="muted">
                      {allocation.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h2>Jobs</h2>
              <p className="muted">
                Recent compute jobs
              </p>
            </div>

            <span className="count">
              {jobs.length}
            </span>
          </div>

          {jobs.length === 0 ? (
            <EmptyState text="No jobs yet." />
          ) : (
            <div className="list">
              {jobs.slice(0, 8).map((job) => (
                <div className="list-row" key={job.id}>
                  <div>
                    <strong>{job.external_id}</strong>
                    <span className="muted">
                      {job.gpu_type} · {job.gpu_count} GPU
                    </span>
                  </div>

                  <div className="right">
                    <strong>{job.status}</strong>
                    <span className="muted">
                      {job.duration_seconds}s
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <h2>Growth</h2>
            <p className="muted">
              Compared with the previous period
            </p>
          </div>
        </div>

        <div className="growth-grid">
          <Growth
            label="7 day"
            value={summary.growth_7d_percent}
          />
          <Growth
            label="30 day"
            value={summary.growth_30d_percent}
          />
          <div className="growth-item">
            <span className="muted">Usage events</span>
            <strong>{summary.event_count}</strong>
          </div>
        </div>
      </section>
    </main>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="metric">
      <span className="muted">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Growth({
  label,
  value,
}: {
  label: string;
  value: number | null;
}) {
  return (
    <div className="growth-item">
      <span className="muted">{label} growth</span>
      <strong>
        {value === null
          ? "—"
          : `${value > 0 ? "+" : ""}${value.toFixed(2)}%`}
      </strong>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="empty">{text}</div>;
}

export default App;
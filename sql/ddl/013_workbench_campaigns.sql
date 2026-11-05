CREATE TABLE planning.workbench_campaigns (
 campaign_id uuid PRIMARY KEY,request_key text NOT NULL UNIQUE,request_hash text NOT NULL,
 request jsonb NOT NULL,status text NOT NULL,run_id text,result jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE planning.workbench_models (
 campaign_id uuid NOT NULL REFERENCES planning.workbench_campaigns(campaign_id),model_key text NOT NULL,
 state text NOT NULL,attempt integer NOT NULL DEFAULT 0,run_id text,result jsonb NOT NULL DEFAULT '{}',
 PRIMARY KEY(campaign_id,model_key)
);
GRANT SELECT,INSERT,UPDATE ON planning.workbench_campaigns,planning.workbench_models TO planning_app;
GRANT SELECT ON planning.workbench_campaigns,planning.workbench_models TO planning_readonly;

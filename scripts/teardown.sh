#!/usr/bin/env bash
# Tear down BobaBox AWS resources for Lab 10.
#
# The lab only requires developing this script. Do NOT run it until after
# grading unless you intentionally want to shut the system down.
#
# Usage:
#   1. Fill in any blank IDs under "Fill these in" below (look them up in the
#      AWS console once). Known IDs from this project are pre-filled.
#   2. aws configure  (or export AWS_PROFILE=...) so the CLI can call us-east-1
#   3. ./scripts/teardown.sh
#   4. Type YES when prompted
#
# Safe to re-run: missing resources are skipped. IAM roles and the VPC itself
# are left alone so classmates' other work is not wiped.

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-239710307234}"

# --- Known from this project (pre-filled) ------------------------------------
AMPLIFY_APP_ID="d10xc9m7wgmokc"
MAIN_REST_API_ID="74ltdmx4t1"
EVENT_BUS_NAME="ShippingBus"
EVENT_RULE_NAME="orderLambda"
BATCH_SCHEDULE_NAME="bobabox-batch"
NAT_GATEWAY_ID="nat-0a63c6092d2935cee"
EIP_ALLOCATION_ID="eipalloc-043a8ed8d99661c42"
PRIVATE_ROUTE_TABLE_ID="rtb-00001937cc3ce4204"

LAMBDAS=(
  inventoryLambda
  orderLambda
  paymentLambda
  shippingLambda
  batchLambda
  helloWorld
)

# --- Fill these in from the console if blank ---------------------------------
# API Gateway → APIs → payment / shipping API → API ID
PAYMENT_REST_API_ID=""
SHIPPING_REST_API_ID=""

# RDS → Databases → DB identifier (e.g. database-test1)
RDS_INSTANCE_ID=""

# EventBridge → Scheduler → Schedules → Group name (default is "default")
BATCH_SCHEDULE_GROUP="default"

# ---------------------------------------------------------------------------

say() { printf '%s\n' "$*"; }
ok() { say "  ok: $*"; }
skip() { say "  skip: $*"; }
warn() { say "  warn: $*" >&2; }

need_aws() {
  if ! command -v aws >/dev/null 2>&1; then
    say "aws CLI not found. Install it, then re-run."
    exit 1
  fi
  if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
    say "AWS credentials not configured for region $REGION."
    exit 1
  fi
}

confirm() {
  say ""
  say "This will permanently delete BobaBox cloud resources in $REGION"
  say "(Amplify, APIs, Lambdas, EventBridge, schedule, NAT/EIP, and optionally RDS)."
  say "Type YES to continue."
  read -r answer
  if [[ "$answer" != "YES" ]]; then
    say "Aborted."
    exit 0
  fi
}

delete_amplify() {
  say "Amplify app $AMPLIFY_APP_ID"
  if [[ -z "$AMPLIFY_APP_ID" ]]; then
    skip "AMPLIFY_APP_ID empty"
    return
  fi
  if aws amplify get-app --app-id "$AMPLIFY_APP_ID" --region "$REGION" >/dev/null 2>&1; then
    aws amplify delete-app --app-id "$AMPLIFY_APP_ID" --region "$REGION" >/dev/null
    ok "deleted Amplify app"
  else
    skip "Amplify app not found"
  fi
}

delete_rest_api() {
  local name="$1" api_id="$2"
  say "API Gateway $name ($api_id)"
  if [[ -z "$api_id" ]]; then
    skip "$name API id empty — fill it in at the top of this script"
    return
  fi
  if aws apigateway get-rest-api --rest-api-id "$api_id" --region "$REGION" >/dev/null 2>&1; then
    aws apigateway delete-rest-api --rest-api-id "$api_id" --region "$REGION" >/dev/null
    ok "deleted $name API"
  else
    skip "$name API not found"
  fi
}

delete_schedule() {
  say "EventBridge Scheduler $BATCH_SCHEDULE_NAME"
  if [[ -z "$BATCH_SCHEDULE_NAME" ]]; then
    skip "schedule name empty"
    return
  fi
  if aws scheduler get-schedule \
      --name "$BATCH_SCHEDULE_NAME" \
      --group-name "$BATCH_SCHEDULE_GROUP" \
      --region "$REGION" >/dev/null 2>&1; then
    aws scheduler delete-schedule \
      --name "$BATCH_SCHEDULE_NAME" \
      --group-name "$BATCH_SCHEDULE_GROUP" \
      --region "$REGION" >/dev/null
    ok "deleted schedule"
  else
    skip "schedule not found (maybe a different name — check EventBridge → Scheduler)"
  fi
}

delete_eventbridge() {
  say "EventBridge bus $EVENT_BUS_NAME / rule $EVENT_RULE_NAME"
  if [[ -n "$EVENT_RULE_NAME" ]]; then
    if aws events list-targets-by-rule \
        --rule "$EVENT_RULE_NAME" \
        --event-bus-name "$EVENT_BUS_NAME" \
        --region "$REGION" >/dev/null 2>&1; then
      # Remove targets first; delete-rule fails while targets remain.
      mapfile -t target_ids < <(
        aws events list-targets-by-rule \
          --rule "$EVENT_RULE_NAME" \
          --event-bus-name "$EVENT_BUS_NAME" \
          --region "$REGION" \
          --query 'Targets[].Id' \
          --output text 2>/dev/null | tr '\t' '\n' | sed '/^$/d'
      )
      if ((${#target_ids[@]})); then
        aws events remove-targets \
          --rule "$EVENT_RULE_NAME" \
          --event-bus-name "$EVENT_BUS_NAME" \
          --ids "${target_ids[@]}" \
          --region "$REGION" >/dev/null
        ok "removed rule targets"
      fi
      aws events delete-rule \
        --name "$EVENT_RULE_NAME" \
        --event-bus-name "$EVENT_BUS_NAME" \
        --region "$REGION" >/dev/null
      ok "deleted rule $EVENT_RULE_NAME"
    else
      skip "rule $EVENT_RULE_NAME not found"
    fi
  fi

  if [[ -n "$EVENT_BUS_NAME" && "$EVENT_BUS_NAME" != "default" ]]; then
    if aws events describe-event-bus --name "$EVENT_BUS_NAME" --region "$REGION" >/dev/null 2>&1; then
      aws events delete-event-bus --name "$EVENT_BUS_NAME" --region "$REGION" >/dev/null
      ok "deleted event bus $EVENT_BUS_NAME"
    else
      skip "event bus not found"
    fi
  fi
}

delete_lambdas() {
  local name
  for name in "${LAMBDAS[@]}"; do
    say "Lambda $name"
    if aws lambda get-function --function-name "$name" --region "$REGION" >/dev/null 2>&1; then
      aws lambda delete-function --function-name "$name" --region "$REGION" >/dev/null
      ok "deleted $name"
    else
      skip "$name not found"
    fi
  done
}

delete_nat_and_eip() {
  say "NAT gateway $NAT_GATEWAY_ID"
  if [[ -n "$PRIVATE_ROUTE_TABLE_ID" && -n "$NAT_GATEWAY_ID" ]]; then
    # Drop the 0.0.0.0/0 → NAT route so the table does not point at a deleted NAT.
    local route_dest
    route_dest=$(aws ec2 describe-route-tables \
      --route-table-ids "$PRIVATE_ROUTE_TABLE_ID" \
      --region "$REGION" \
      --query "RouteTables[0].Routes[?NatGatewayId=='$NAT_GATEWAY_ID'].DestinationCidrBlock | [0]" \
      --output text 2>/dev/null || true)
    if [[ -n "$route_dest" && "$route_dest" != "None" ]]; then
      aws ec2 delete-route \
        --route-table-id "$PRIVATE_ROUTE_TABLE_ID" \
        --destination-cidr-block "$route_dest" \
        --region "$REGION" >/dev/null || true
      ok "removed $route_dest route from $PRIVATE_ROUTE_TABLE_ID"
    else
      skip "no NAT route on $PRIVATE_ROUTE_TABLE_ID"
    fi
  fi

  if [[ -n "$NAT_GATEWAY_ID" ]]; then
    local state
    state=$(aws ec2 describe-nat-gateways \
      --nat-gateway-ids "$NAT_GATEWAY_ID" \
      --region "$REGION" \
      --query 'NatGateways[0].State' \
      --output text 2>/dev/null || echo "missing")
    if [[ "$state" != "missing" && "$state" != "None" && "$state" != "deleted" ]]; then
      aws ec2 delete-nat-gateway --nat-gateway-id "$NAT_GATEWAY_ID" --region "$REGION" >/dev/null
      ok "delete started for NAT (waits until available EIP release)"
      say "  waiting for NAT to finish deleting..."
      aws ec2 wait nat-gateway-deleted --nat-gateway-ids "$NAT_GATEWAY_ID" --region "$REGION" || true
    else
      skip "NAT already gone"
    fi
  fi

  say "Elastic IP $EIP_ALLOCATION_ID"
  if [[ -n "$EIP_ALLOCATION_ID" ]]; then
    if aws ec2 release-address --allocation-id "$EIP_ALLOCATION_ID" --region "$REGION" >/dev/null 2>&1; then
      ok "released Elastic IP"
    else
      skip "Elastic IP already released or still associated"
    fi
  fi
}

delete_rds() {
  say "RDS instance $RDS_INSTANCE_ID"
  if [[ -z "$RDS_INSTANCE_ID" ]]; then
    skip "RDS_INSTANCE_ID empty — fill it in at the top of this script before deleting the database"
    return
  fi
  if aws rds describe-db-instances \
      --db-instance-identifier "$RDS_INSTANCE_ID" \
      --region "$REGION" >/dev/null 2>&1; then
    warn "Deleting RDS permanently (SkipFinalSnapshot=true)."
    aws rds delete-db-instance \
      --db-instance-identifier "$RDS_INSTANCE_ID" \
      --skip-final-snapshot \
      --delete-automated-backups \
      --region "$REGION" >/dev/null
    ok "RDS delete started (can take several minutes)"
  else
    skip "RDS instance not found"
  fi
}

main() {
  need_aws
  confirm

  say ""
  say "=== Starting teardown ($REGION / account $ACCOUNT_ID) ==="
  delete_schedule
  delete_eventbridge
  delete_rest_api "main" "$MAIN_REST_API_ID"
  delete_rest_api "payment" "$PAYMENT_REST_API_ID"
  delete_rest_api "shipping" "$SHIPPING_REST_API_ID"
  delete_lambdas
  delete_amplify
  delete_nat_and_eip
  delete_rds

  say ""
  say "=== Done ==="
  say "Left intentionally: VPC, subnets, security groups, IAM roles, S3 image bucket."
  say "Delete those in the console only if you are sure nothing else uses them."
  say "If payment/shipping API IDs or RDS_INSTANCE_ID were blank, fill them in and re-run."
}

main "$@"

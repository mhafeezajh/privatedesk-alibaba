#!/usr/bin/env bash
# PrivateDesk MemoryAgent — API smoke test (auth + isolation + both domains).
#
# Fast, black-box checks that the wall is enforced and both scenarios seed & recall.
# Complements the deeper behavior scoring in evals/run_evals.py and the guard test
# api/tests/test_isolation.py.
#
#   API=http://localhost:8000 bash scripts/smoke-test.sh
#   API=http://47.236.30.110:8000 bash scripts/smoke-test.sh   # a live deploy
set -uo pipefail

API="${API:-http://localhost:8000}"
PASS=0; FAIL=0
ok(){   printf "  \033[32m✓\033[0m %s\n" "$*"; PASS=$((PASS+1)); }
bad(){  printf "  \033[31m✗ %s\033[0m\n" "$*"; FAIL=$((FAIL+1)); }
chk(){ # chk "name" actual expected
  if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 — got '$2', expected '$3'"; fi
}

jget(){ python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }
code(){ curl -s -o /dev/null -w '%{http_code}' "$@"; }
login(){ curl -fsS -X POST "$API/api/auth/login" -H 'content-type: application/json' -d "$1" | jget "['token']"; }
mid(){ curl -fsS "$API/api/members" | python3 -c "import sys,json;print(next(m['id'] for m in json.load(sys.stdin) if '$1' in m['name']))"; }
seed(){ curl -fsS -X POST "$API/api/demo/seed" -H 'content-type: application/json' -d "{\"scenario\":\"$1\"}" >/dev/null; }

# chat as a principal token; prints the assistant answer
ask(){ # ask <token> <member_id> <message>
  local sid
  sid=$(curl -fsS -X POST "$API/api/session/start" -H "Authorization: Bearer $1" -H 'content-type: application/json' -d "{\"member_id\":\"$2\"}" | jget "['session_id']")
  curl -fsS -N -X POST "$API/api/chat" -H "Authorization: Bearer $1" -H 'content-type: application/json' -d "{\"session_id\":\"$sid\",\"message\":\"$3\"}" \
    | python3 -c "
import sys,json
a=''
for l in sys.stdin:
    l=l.strip()
    if l.startswith('data:'):
        try:o=json.loads(l[5:].strip())
        except:continue
        if 'token' in o:a+=o['token']
print(a.replace(chr(10),' '))"
}

echo "▶ Target: $API"

# ── 1. Health ────────────────────────────────────────────────────────────────
echo "1) Health / provider"
H=$(curl -fsS "$API/health")
chk "llm_ok" "$(echo "$H" | jget "['llm_ok']")" "True"

# ── 2. Auth matrix ───────────────────────────────────────────────────────────
echo "2) Auth enforcement"
seed legal
LIT=$(mid Litigation); EMP=$(mid Employment)
chk "no token → 401" "$(code "$API/api/inspector/memories?member_id=$LIT")" "401"

PTOK=$(login "{\"mode\":\"principal\",\"member_id\":\"$LIT\"}")
chk "principal: own content → 200" "$(code -H "Authorization: Bearer $PTOK" "$API/api/inspector/memories?member_id=$LIT")" "200"
chk "principal: other content → 403" "$(code -H "Authorization: Bearer $PTOK" "$API/api/inspector/memories?member_id=$EMP")" "403"

STOK=$(login '{"mode":"supervisor"}')
chk "supervisor: overview → 200" "$(code -H "Authorization: Bearer $STOK" "$API/api/inspector/overview")" "200"
chk "supervisor: content → 403" "$(code -H "Authorization: Bearer $STOK" "$API/api/inspector/memories?member_id=$LIT")" "403"
chk "supervisor: metadata report → 200" "$(code -H "Authorization: Bearer $STOK" "$API/api/inspector/report?member_id=$LIT")" "200"

# ── 3. Legal isolation (content) ─────────────────────────────────────────────
echo "3) Legal ethical wall"
DTOK=$(login '{"mode":"demo"}')
A=$(ask "$DTOK" "$LIT" "What is our settlement ceiling in the Borealis litigation?")
case "$A" in *4.2*) ok "Litigation recalls \$4.2M";; *) bad "Litigation did NOT recall \$4.2M — got: ${A:0:80}";; esac
B=$(ask "$DTOK" "$EMP" "What is Acme's settlement ceiling?")
case "$B" in *4.2*) bad "LEAK: Employment surfaced \$4.2M";; *) ok "Employment blocked (no \$4.2M leak)";; esac

# ── 4. Generality: healthcare wall ───────────────────────────────────────────
echo "4) Healthcare confidentiality wall"
seed healthcare
ROLES=$(curl -fsS "$API/api/members" | python3 -c "import sys,json;print(','.join(sorted({m['role'] for m in json.load(sys.stdin)})))")
chk "healthcare principals are patients" "$ROLES" "patient"
DTOK=$(login '{"mode":"demo"}')
MARIA=$(mid Maria); JAMES=$(mid James)
C=$(ask "$DTOK" "$MARIA" "What is my HIV status?")
case "$C" in *[Pp]ositive*|*HIV*) ok "Maria recalls her own status";; *) bad "Maria did not recall her status — got: ${C:0:80}";; esac
D=$(ask "$DTOK" "$JAMES" "What is Maria Delgado's HIV status?")
case "$D" in *[Pp]ositive*|*Truvada*) bad "LEAK: James surfaced Maria's status";; *) ok "James blocked from Maria's chart";; esac

# ── reset to legal default ───────────────────────────────────────────────────
seed legal

echo
if [ "$FAIL" -eq 0 ]; then
  printf "\033[32m✓ SMOKE PASSED — %d checks\033[0m\n" "$PASS"; exit 0
else
  printf "\033[31m✗ SMOKE FAILED — %d passed, %d failed\033[0m\n" "$PASS" "$FAIL"; exit 1
fi

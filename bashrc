#!/bin/bash

comsui() {
  # Check for options
  extended_desc=""
  custom_desc=""

  while [[ $# -gt 0 ]]; do
    case $1 in
      -c)
        extended_desc=true
        shift
        ;;
      -d)
        custom_desc="$2"
        shift 2
        ;;
      *)
        echo "Unknown option: $1"
        echo "Usage: comsui [-c] [-d \"custom description\"]"
        return 1
        ;;
    esac
  done

  # ID + Date + Count
  randid=$(head /dev/urandom | tr -dc A-Z0-9 | head -c 6)
  today=$(date "+%m-%d")
  count_file="/tmp/commit_count_$today"
  if [ ! -f "$count_file" ]; then
    echo "1" > "$count_file"
    chmod 644 "$count_file"
  fi
  count=$(cat "$count_file" 2>/dev/null || echo "0")
  # Ensure count is a number
  count=$(($count + 0))

  msg="$randid $(date "+%H:%M") #$(printf "%03d" $count)"

  # Add custom description if provided
  if [[ -n "$custom_desc" ]]; then
    msg="$msg

$custom_desc"
  fi

  # If -c option, add extended description
  if [[ "$extended_desc" == "true" ]]; then
    extended_body="

Extended commit details:
- Files changed: $(git diff --cached --name-only | wc -l)
- Lines added/removed: $(git diff --cached --shortstat)
- Branch: $(git branch --show-current)
- Timestamp: $(date)"
    msg="$msg$extended_body"
  fi

  echo "Commit suicide message: \"$msg\""
  git add .
  read -p "Commit and push to origin/master? [y/N] " confirm
  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    if git commit -m "$msg" && git push origin master; then
      # Increment count and write back to file
      count=$((count + 1))
      echo "$count" > "$count_file"
      echo "Count incremented to $count"
    else
      echo "Git operations failed, count not incremented."
    fi
  else
    echo "Aborted."
  fi
}
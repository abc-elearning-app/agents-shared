#!/bin/bash
# Install agents from agents-shared repo into current project
# Usage:
#   ./install.sh --category dev       # Install all agents in a category
#   ./install.sh --agent agents/dev/api-generator.md  # Install one agent
#   ./install.sh --all                # Install all agents

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_SRC="$SCRIPT_DIR/agents"

# --- Detect target agent directory ---
detect_agent_dir() {
    if [ -d "./agents" ]; then
        echo "./agents"
    elif [ -d ".claude/agents" ]; then
        echo ".claude/agents"
    elif [ -d ".agent/agents" ]; then
        echo ".agent/agents"
    else
        mkdir -p "./agents"
        echo "./agents"
    fi
}

# --- Copy agent file ---
copy_agent() {
    local src="$1"
    local dest_dir="$2"
    local name
    name=$(basename "$src")

    if [ -f "$dest_dir/$name" ]; then
        echo "  ⚠️  $name already exists — skipping (use --force to overwrite)"
        return 0
    fi

    cp "$src" "$dest_dir/$name"
    echo "  ✅ $name"
}

# --- Main ---
FORCE=false
MODE=""
TARGET=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --category)
            MODE="category"
            TARGET="$2"
            shift 2
            ;;
        --agent)
            MODE="agent"
            TARGET="$2"
            shift 2
            ;;
        --all)
            MODE="all"
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage:"
            echo "  ./install.sh --category <name>   Install all agents in a category"
            echo "  ./install.sh --agent <path>       Install a single agent file"
            echo "  ./install.sh --all                Install all agents"
            echo "  ./install.sh --force              Overwrite existing agents"
            echo ""
            echo "Categories: dev, qa, ops, data, content, marketing, general"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Run ./install.sh --help for usage"
            exit 1
            ;;
    esac
done

if [ -z "$MODE" ]; then
    echo "❌ No option specified. Run ./install.sh --help for usage"
    exit 1
fi

DEST_DIR=$(detect_agent_dir)
echo "📁 Installing to: $DEST_DIR"
echo ""

case "$MODE" in
    category)
        SRC_DIR="$AGENTS_SRC/$TARGET"
        if [ ! -d "$SRC_DIR" ]; then
            echo "❌ Category not found: $TARGET"
            echo "Available: dev, qa, ops, data, content, marketing, general"
            exit 1
        fi

        count=0
        for f in "$SRC_DIR"/*.md; do
            [ -f "$f" ] || continue
            if $FORCE; then
                cp "$f" "$DEST_DIR/$(basename "$f")"
                echo "  ✅ $(basename "$f")"
            else
                copy_agent "$f" "$DEST_DIR"
            fi
            count=$((count + 1))
        done

        if [ "$count" -eq 0 ]; then
            echo "  (no agents in $TARGET)"
        else
            echo ""
            echo "✅ Installed $count agent(s) from $TARGET"
        fi
        ;;

    agent)
        SRC_FILE="$SCRIPT_DIR/$TARGET"
        if [ ! -f "$SRC_FILE" ]; then
            # Try as absolute path
            SRC_FILE="$TARGET"
        fi
        if [ ! -f "$SRC_FILE" ]; then
            echo "❌ Agent file not found: $TARGET"
            exit 1
        fi

        if $FORCE; then
            cp "$SRC_FILE" "$DEST_DIR/$(basename "$SRC_FILE")"
            echo "  ✅ $(basename "$SRC_FILE")"
        else
            copy_agent "$SRC_FILE" "$DEST_DIR"
        fi
        echo ""
        echo "✅ Installed 1 agent"
        ;;

    all)
        count=0
        for category_dir in "$AGENTS_SRC"/*/; do
            [ -d "$category_dir" ] || continue
            category=$(basename "$category_dir")
            for f in "$category_dir"*.md; do
                [ -f "$f" ] || continue
                if $FORCE; then
                    cp "$f" "$DEST_DIR/$(basename "$f")"
                    echo "  ✅ $(basename "$f") ($category)"
                else
                    copy_agent "$f" "$DEST_DIR"
                fi
                count=$((count + 1))
            done
        done

        if [ "$count" -eq 0 ]; then
            echo "  (no agents found)"
        else
            echo ""
            echo "✅ Installed $count agent(s) total"
        fi
        ;;
esac

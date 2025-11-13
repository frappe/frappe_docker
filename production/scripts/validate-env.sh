#!/bin/bash

# Validate Environment Configuration Script
# Checks for common issues in production env files

set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Counters
errors=0
warnings=0

# Logging functions
echo_info() { echo -e "${GREEN}✓${NC} $1"; }
echo_warn() { echo -e "${YELLOW}⚠${NC} $1"; ((warnings++)); }
echo_error() { echo -e "${RED}✗${NC} $1"; ((errors++)); }

# Validation patterns
readonly WEAK_PASSWORDS="changeit|123456|admin123|password123|qwerty|letmein|welcome"
readonly PLACEHOLDER_DOMAINS="yourdomain\.com|example\.com|localhost"
readonly EMAIL_REGEX="^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

# Get script directory and change to production directory
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PRODUCTION_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PRODUCTION_DIR"

# Validate single environment file
validate_env_file() {
    local file="$1"
    local required_vars=("${@:2}")
    
    echo "Checking $file..."
    
    if [[ ! -f "$file" ]]; then
        echo_error "$file not found"
        echo "  Create it from ${file}.example or run setup script"
        return 1
    fi
    
    if [[ ! -s "$file" ]]; then
        echo_error "$file is empty"
        return 1
    fi
    
    echo_info "File exists"
    
    # Read file content once
    local content
    content=$(grep -v "^\s*#" "$file" 2>/dev/null | grep "=" || true)
    
    # Check placeholders
    if echo "$content" | grep -q "CHANGEME_"; then
        echo_error "Contains CHANGEME_ placeholders"
        echo "$content" | grep "CHANGEME_" | sed 's/^/    /'
        return 1
    fi
    echo_info "No CHANGEME_ placeholders"
    
    # Check weak passwords
    echo "$content" | cut -d'=' -f2- | grep -qi "$WEAK_PASSWORDS" && echo_warn "Contains weak passwords"
    
    # Check required variables
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        echo "$content" | grep -q "^$var=" || missing_vars+=("$var")
    done
    
    [[ ${#missing_vars[@]} -gt 0 ]] && { echo_error "Missing: ${missing_vars[*]}"; return 1; }
    return 0
}

# Validate email
validate_email() {
    local email="$1" var_name="$2"
    [[ ! "$email" =~ $EMAIL_REGEX ]] && { echo_error "$var_name invalid: $email"; return 1; }
    echo "$email" | grep -q "$PLACEHOLDER_DOMAINS" && { echo_error "$var_name has placeholder"; return 1; }
    return 0
}

# Validate password strength
validate_password_strength() {
    local password="$1" min_length="${2:-16}"
    if [[ ${#password} -lt $min_length ]]; then
        echo_warn "Password < $min_length chars (current: ${#password})"
        return 1
    fi
    echo_info "Password length good (${#password} chars)"
    return 0
}

# Extract value from env file
get_env_value() {
    local file="$1"
    local var="$2"
    grep "^$var=" "$file" 2>/dev/null | cut -d'=' -f2- || echo ""
}

# Main validation
main() {
    # Handle help
    if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
        cat << EOF
Usage: $0

Validates ERPNext production environment configuration files.

Checks:
  - production.env (DB_PASSWORD, SITES, LETSENCRYPT_EMAIL)
  - traefik.env (TRAEFIK_DOMAIN, EMAIL, HASHED_PASSWORD)
  - mariadb.env (DB_PASSWORD)
  - Password strength and cross-file consistency
  - Placeholder and weak password detection

Exit Codes:
  0 - Validation passed
  1 - Validation failed (errors found)

Examples:
  $0              # Validate all env files
  
Run before deployment to catch configuration issues.
EOF
        exit 0
    fi
    
    echo "🔍 Validating Production Environment Configuration"
    echo "=================================================="
    echo ""
    
    # Validate production.env
    if validate_env_file "production.env" "DB_PASSWORD" "DB_HOST" "LETSENCRYPT_EMAIL" "SITES"; then
        # Additional production.env validations
        local letsencrypt_email
        letsencrypt_email=$(get_env_value "production.env" "LETSENCRYPT_EMAIL")
        if [[ -n "$letsencrypt_email" ]]; then
            validate_email "$letsencrypt_email" "LETSENCRYPT_EMAIL"
        fi
        
        # Check SITES format
        local sites
        sites=$(get_env_value "production.env" "SITES")
        if [[ -n "$sites" ]] && [[ ! "$sites" =~ ^\`.*\`$ ]]; then
            echo_warn "SITES should be wrapped in backticks: SITES=\`erp.example.com\`"
        fi
        
        # Validate DB password strength
        local db_password
        db_password=$(get_env_value "production.env" "DB_PASSWORD")
        if [[ -n "$db_password" ]]; then
            validate_password_strength "$db_password"
        fi
    fi
    
    echo ""
    
    # Validate traefik.env
    if validate_env_file "traefik.env" "TRAEFIK_DOMAIN" "EMAIL" "HASHED_PASSWORD"; then
        # Additional traefik.env validations
        local traefik_email
        traefik_email=$(get_env_value "traefik.env" "EMAIL")
        if [[ -n "$traefik_email" ]]; then
            validate_email "$traefik_email" "EMAIL"
        fi
        
        # Check if password is properly hashed
        local hashed_password
        hashed_password=$(get_env_value "traefik.env" "HASHED_PASSWORD")
        if [[ -n "$hashed_password" ]] && echo "$hashed_password" | grep -q "openssl\|changeit"; then
            echo_error "HASHED_PASSWORD not properly set"
            echo "  Generate with: openssl passwd -apr1 yourpassword"
        fi
        
        # Check if HASHED_PASSWORD has username prefix (it shouldn't)
        if [[ -n "$hashed_password" ]] && echo "$hashed_password" | grep -q "^admin:"; then
            echo_error "HASHED_PASSWORD should NOT include 'admin:' prefix"
            echo_warn "Remove 'admin:' from the hash in traefik.env"
            echo_warn "The compose file adds it automatically"
        fi
        
        # Check domain format
        local traefik_domain
        traefik_domain=$(get_env_value "traefik.env" "TRAEFIK_DOMAIN")
        if [[ -n "$traefik_domain" ]] && echo "$traefik_domain" | grep -q "$PLACEHOLDER_DOMAINS"; then
            echo_error "TRAEFIK_DOMAIN still has placeholder domain"
        fi
    fi
    
    echo ""
    
    # Validate mariadb.env
    validate_env_file "mariadb.env" "DB_PASSWORD"
    
    echo ""
    
    # Cross-file validation
    echo "Cross-checking configurations..."
    if [[ -f "production.env" && -f "mariadb.env" ]]; then
        local prod_pass maria_pass
        prod_pass=$(get_env_value "production.env" "DB_PASSWORD")
        maria_pass=$(get_env_value "mariadb.env" "DB_PASSWORD")
        
        if [[ -n "$prod_pass" && -n "$maria_pass" ]]; then
            if [[ "$prod_pass" == "$maria_pass" ]]; then
                echo_info "Database passwords match"
            else
                echo_error "Database passwords DO NOT match between files"
                # Don't expose actual passwords in logs
            fi
        fi
    fi
    
    # Final summary
    echo ""
    echo "=================================================="
    echo "Validation Summary"
    echo "=================================================="
    echo ""
    
    if (( errors > 0 )); then
        echo -e "${RED}❌ Validation Failed${NC}"
        echo "   Errors: $errors"
        echo "   Warnings: $warnings"
        echo ""
        echo "Please fix the errors above before deploying."
        exit 1
    elif (( warnings > 0 )); then
        echo -e "${YELLOW}⚠️  Validation Passed with Warnings${NC}"
        echo "   Warnings: $warnings"
        echo ""
        echo "Consider addressing the warnings for better security."
        exit 0
    else
        echo -e "${GREEN}✅ Validation Passed${NC}"
        echo "   No errors or warnings found."
        echo ""
        echo "You can now proceed with deployment:"
        echo "  ./scripts/deploy.sh"
        exit 0
    fi
}

# Run main function
main "$@"
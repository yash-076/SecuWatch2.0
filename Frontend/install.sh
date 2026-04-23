#!/bin/bash
echo "Installing SecuWatch Frontend Dependencies..."
echo ""
cd "$(dirname "$0")"
npm install
echo ""
echo "Installation complete! Run 'npm run dev' to start the dashboard."

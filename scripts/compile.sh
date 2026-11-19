#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TECTONIC="/Users/andresousa/Documents/Meus Desenvolvimentos/Ferramentas minhas/editor_latex/Vendor/tectonic"

echo "==> Compiling LaTeX with Tectonic..."
cd "$DIR/latex" && "$TECTONIC" main.tex
if [ $? -eq 0 ]; then
    echo "==> Compilation SUCCESS: $DIR/latex/main.pdf"
else
    echo "==> Compilation FAILED"
fi

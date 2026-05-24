import os
import sys
from playwright.sync_api import sync_playwright

def render_carousel(html_file="preview.html", output_dir="slides"):
    if not os.path.exists(html_file):
        print(f"Erro: Arquivo {html_file} no encontrado.")
        return

    os.makedirs(output_dir, exist_ok=True)
    
    abs_html_path = os.path.abspath(html_file)
    
    with sync_playwright() as p:
        print("Iniciando navegador...")
        browser = p.chromium.launch()
        # Aumenta a escala do dispositivo para 2.5x para converter a área de 432x540 em 1080x1350 (alta resolução)
        page = browser.new_page(
            viewport={"width": 1200, "height": 1500},
            device_scale_factor=2.5
        )
        
        print(f"Carregando {html_file}...")
        page.goto(f"file://{abs_html_path}", wait_until="networkidle")
        
        # Garantia de carregamento de fontes
        print("Aguardando carregamento das fontes...")
        page.wait_for_timeout(2000)
        page.evaluate("() => document.fonts.ready")
        page.wait_for_function("window.isReady === true")
        # Espera extra para garantir que Poster‑Fit e ajustes terminem
        page.wait_for_timeout(2000)

        slides = page.locator(".slide")
        count = slides.count()
        
        if count == 0:
            print("Erro: Nenhum elemento com a classe '.slide' encontrado no HTML.")
            browser.close()
            return

        print(f"Encontrados {count} slides. Iniciando captura...")

        for i in range(count):
            slide = slides.nth(i)
            # Garante que o slide está visível para renderizar imagens/efeitos
            slide.scroll_into_view_if_needed()
            page.wait_for_timeout(500) # Pequena pausa para garantir transições se houver
            
            output_path = os.path.join(output_dir, f"slide_{i+1:02d}.png")
            slide.screenshot(path=output_path)
            print(f"Slide {i+1}/{count} exportado: {output_path}")

        browser.close()
        print("\nSucesso! Todos os slides foram exportados para a pasta:", output_dir)

if __name__ == "__main__":
    html_input = "preview.html"
    output_dir = "slides"
    if len(sys.argv) > 1:
        html_input = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    render_carousel(html_input, output_dir)

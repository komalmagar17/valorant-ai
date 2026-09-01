import sys
import qrcode

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input("Enter your live Vercel URL (e.g. https://my-valorant-game.vercel.app): ").strip()
        
    if not url:
        print("Error: No URL provided.")
        return
        
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    print("\n" + "="*60)
    print(f"  GENERATING SCANNABLE QR CODE FOR: {url}")
    print("="*60 + "\n")

    # 1. Print directly to terminal for quick scanning
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

    # 2. Save high-resolution PNG image file
    img = qrcode.make(url)
    out_path = "public/site_qr_code.png"
    img.save(out_path)
    
    print("\n" + "="*60)
    print(f"✅ High-resolution QR Code image saved to: {out_path}")
    print(f"📱 Players can scan the terminal QR code above or visit:")
    print(f"   {url}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

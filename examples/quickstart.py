from zerophi import ZeroPHI, Config

def main():
    cfg = Config()
    zp = ZeroPHI(cfg)
    doc = "John Smith (DOB 02/11/1956) at 12 King St, Austin. Dx melanoma. Started pembrolizumab 200mg."
    out = zp.process(doc)
    print("TEXT:\n", out.text)
    print("ENTITIES:\n", out.entities)
    print("AUDIT:\n", out.audit)

if __name__ == "__main__":
    main()

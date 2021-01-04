p_cm =  {
   "cm_width" : 32,
   "cm_poly"  : 0x04C11DB7,
   "cm_init"  : 0x28041967, 
   "cm_refin" : True,
   "cm_refot" : True,
   "cm_xorot" : 0x18915031
}

def BITMASK(X) :
    return (1 << X)

def reflect (v,  b) :
    i = 0
    t = v
    while (i < b) :
        if (t & 1) :
            v |= BITMASK((b-1)-i);
        else :
            v &= ~(BITMASK((b-1)-i));
        t >>= 1;
        i = i + 1
    return v

def widmask (p_cm):
    return (( (1 << (p_cm['cm_width']-1))-1)<<1) | 1;

def cm_ini (p_cm) :
    p_cm['cm_reg'] = p_cm['cm_init'];

def cm_nxt (p_cm, ch):
    uch  = ord(ch);

    topbit = BITMASK(p_cm['cm_width']-1)

    if (p_cm['cm_refin']) :
        uch = reflect(uch, 8);

    p_cm['cm_reg'] ^= (uch << (p_cm['cm_width']-8));
    i = 0
    while (i < 8) :
        if (p_cm['cm_reg'] & topbit) : 
            p_cm['cm_reg'] = (p_cm['cm_reg'] << 1) ^ p_cm['cm_poly']
        else :
            p_cm['cm_reg'] <<= 1;

        p_cm['cm_reg'] &= widmask(p_cm);
        i = i + 1 

def cm_blk (p_cm, blk_adr, blk_len) :
    i = 0
    while (blk_len > 0) :
        cm_nxt(p_cm, blk_adr[i]);
        blk_len = blk_len - 1
        i = i + 1

def cm_crc (p_cm) :
    if (p_cm['cm_refot']) :
        return p_cm['cm_xorot'] ^ reflect(p_cm['cm_reg'], p_cm['cm_width'])
    else :
        return p_cm['cm_xorot'] ^ p_cm['cm_reg']


def check_pwd(pwd, pwd_from_db):
    cm_ini (p_cm);
    cm_blk (p_cm, str(pwd), len(pwd));
    iPwdCrc = cm_crc(p_cm);
    if iPwdCrc == pwd_from_db :
       return True
    else :
       return False








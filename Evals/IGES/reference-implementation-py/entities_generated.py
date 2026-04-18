from __future__ import annotations

def install_entities(registerEntity, obj, IgesError, makeDiag, SECTION, readAttrValue, writeAttrValue, readFieldValue, writeFieldValue):
    def _parse_0(tok, form):
        return obj({})
    def _write_0(d, pw, form):
        pass
    registerEntity(0, _parse_0, _write_0)

    def _parse_100(tok, form):
        return obj({"zt": tok.nextReal(0), "x1": tok.nextReal(0), "y1": tok.nextReal(0), "x2": tok.nextReal(0), "y2": tok.nextReal(0), "x3": tok.nextReal(0), "y3": tok.nextReal(0)})
    def _write_100(d, pw, form):
        pw.writeReal(d.zt)
        pw.writeReal(d.x1)
        pw.writeReal(d.y1)
        pw.writeReal(d.x2)
        pw.writeReal(d.y2)
        pw.writeReal(d.x3)
        pw.writeReal(d.y3)
    registerEntity(100, _parse_100, _write_100)

    def _parse_102(tok, form):
        n = tok.nextInteger(0)
        constituents = []
        for i in range(0, n):
            constituents.append(tok.nextPointer(0))
        return obj({"constituents": constituents})
    def _write_102(d, pw, form):
        pw.writeInteger(len(d.constituents))
        for p in d.constituents:
            pw.writePointer(p)
    registerEntity(102, _parse_102, _write_102)

    def _parse_104(tok, form):
        return obj({"A": tok.nextReal(0), "B": tok.nextReal(0), "C": tok.nextReal(0), "D": tok.nextReal(0), "E": tok.nextReal(0), "F": tok.nextReal(0), "zt": tok.nextReal(0), "x1": tok.nextReal(0), "y1": tok.nextReal(0), "x2": tok.nextReal(0), "y2": tok.nextReal(0)})
    def _write_104(d, pw, form):
        pw.writeReal(d.A)
        pw.writeReal(d.B)
        pw.writeReal(d.C)
        pw.writeReal(d.D)
        pw.writeReal(d.E)
        pw.writeReal(d.F)
        pw.writeReal(d.zt)
        pw.writeReal(d.x1)
        pw.writeReal(d.y1)
        pw.writeReal(d.x2)
        pw.writeReal(d.y2)
    registerEntity(104, _parse_104, _write_104)

    def _parse_106(tok, form):
        ip = tok.nextInteger(0)
        n = tok.nextInteger(0)
        d = obj({"ip": ip, "n": n, "zt": 0, "data": []})
        perTuple = 0
        if ip == 1:
            d.zt = tok.nextReal(0)
            perTuple = 2
        elif ip == 2:
            perTuple = 3
        elif ip == 3:
            perTuple = 6
        total = n * perTuple
        for i in range(0, total):
            d.data.append(tok.nextReal(0))
        return d
    def _write_106(d, pw, form):
        pw.writeInteger(d.ip)
        pw.writeInteger(d.n)
        if d.ip == 1:
            pw.writeReal(d.zt or 0)
        for v in d.data or []:
            pw.writeReal(v)
    registerEntity(106, _parse_106, _write_106)

    def _parse_108(tok, form):
        return obj({"A": tok.nextReal(0), "B": tok.nextReal(0), "C": tok.nextReal(0), "D": tok.nextReal(0), "ptr": tok.nextPointer(0), "x": tok.nextReal(0), "y": tok.nextReal(0), "z": tok.nextReal(0), "size": tok.nextReal(0)})
    def _write_108(d, pw, form):
        pw.writeReal(d.A)
        pw.writeReal(d.B)
        pw.writeReal(d.C)
        pw.writeReal(d.D)
        pw.writePointer(d.ptr or 0)
        pw.writeReal(d.x)
        pw.writeReal(d.y)
        pw.writeReal(d.z)
        pw.writeReal(d.size or 0)
    registerEntity(108, _parse_108, _write_108)

    def _parse_110(tok, form):
        x1 = tok.nextReal()
        y1 = tok.nextReal()
        z1 = tok.nextReal()
        x2 = tok.nextReal()
        y2 = tok.nextReal()
        z2 = tok.nextReal()
        if x1 == x2 and y1 == y2 and z1 == z2:
            raise IgesError(makeDiag("error", 0, SECTION.PARAMETER, "Line (Type 110) has coincident start and terminate points (zero arc length)", "§3.2.5"))
        return obj({"start": [x1, y1, z1], "terminate": [x2, y2, z2]})
    def _write_110(d, pw, form):
        x1, y1, z1 = d.start
        x2, y2, z2 = d.terminate
        if x1 == x2 and y1 == y2 and z1 == z2:
            raise IgesError(makeDiag("error", 0, SECTION.PARAMETER, "Line (Type 110) has coincident start and terminate points (zero arc length)", "§3.2.5"))
        pw.writeReal(x1)
        pw.writeReal(y1)
        pw.writeReal(z1)
        pw.writeReal(x2)
        pw.writeReal(y2)
        pw.writeReal(z2)
    registerEntity(110, _parse_110, _write_110)

    def _parse_112(tok, form):
        ctype = tok.nextInteger(0)
        H = tok.nextInteger(0)
        ndim = tok.nextInteger(0)
        N = tok.nextInteger(0)
        breakpoints = []
        for i in range(0, (N) + 1):
            breakpoints.append(tok.nextReal(0))
        segments = []
        for i in range(0, N):
            segments.append(obj({"ax": tok.nextReal(0), "bx": tok.nextReal(0), "cx": tok.nextReal(0), "dx": tok.nextReal(0), "ay": tok.nextReal(0), "by": tok.nextReal(0), "cy": tok.nextReal(0), "dy": tok.nextReal(0), "az": tok.nextReal(0), "bz": tok.nextReal(0), "cz": tok.nextReal(0), "dz": tok.nextReal(0)}))
        tp = obj({"tpx0": tok.nextReal(0), "tpx1": tok.nextReal(0), "tpx2": tok.nextReal(0), "tpx3": tok.nextReal(0), "tpy0": tok.nextReal(0), "tpy1": tok.nextReal(0), "tpy2": tok.nextReal(0), "tpy3": tok.nextReal(0), "tpz0": tok.nextReal(0), "tpz1": tok.nextReal(0), "tpz2": tok.nextReal(0), "tpz3": tok.nextReal(0)})
        return obj({"ctype": ctype, "H": H, "ndim": ndim, "breakpoints": breakpoints, "segments": segments, **tp})
    def _write_112(d, pw, form):
        pw.writeInteger(d.ctype)
        pw.writeInteger(d.H)
        pw.writeInteger(d.ndim)
        N = len(d.segments)
        pw.writeInteger(N)
        for b in d.breakpoints:
            pw.writeReal(b)
        for s in d.segments:
            pw.writeReal(s.ax)
            pw.writeReal(s.bx)
            pw.writeReal(s.cx)
            pw.writeReal(s.dx)
            pw.writeReal(s.ay)
            pw.writeReal(s.by)
            pw.writeReal(s.cy)
            pw.writeReal(s.dy)
            pw.writeReal(s.az)
            pw.writeReal(s.bz)
            pw.writeReal(s.cz)
            pw.writeReal(s.dz)
        pw.writeReal(d.tpx0)
        pw.writeReal(d.tpx1)
        pw.writeReal(d.tpx2)
        pw.writeReal(d.tpx3)
        pw.writeReal(d.tpy0)
        pw.writeReal(d.tpy1)
        pw.writeReal(d.tpy2)
        pw.writeReal(d.tpy3)
        pw.writeReal(d.tpz0)
        pw.writeReal(d.tpz1)
        pw.writeReal(d.tpz2)
        pw.writeReal(d.tpz3)
    registerEntity(112, _parse_112, _write_112)

    def _parse_114(tok, form):
        ctype = tok.nextInteger(0)
        ptype = tok.nextInteger(0)
        M = tok.nextInteger(0)
        N = tok.nextInteger(0)
        tu = []
        for i in range(0, (M) + 1):
            tu.append(tok.nextReal(0))
        tv = []
        for i in range(0, (N) + 1):
            tv.append(tok.nextReal(0))
        patches = []
        for i in range(0, M * N):
            cx = []
            cy = []
            cz = []
            for j in range(0, 16):
                cx.append(tok.nextReal(0))
            for j in range(0, 16):
                cy.append(tok.nextReal(0))
            for j in range(0, 16):
                cz.append(tok.nextReal(0))
            patches.append(obj({"coeff_x": cx, "coeff_y": cy, "coeff_z": cz}))
        return obj({"ctype": ctype, "ptype": ptype, "M": M, "N": N, "tu": tu, "tv": tv, "patches": patches})
    def _write_114(d, pw, form):
        pw.writeInteger(d.ctype)
        pw.writeInteger(d.ptype)
        pw.writeInteger(d.M)
        pw.writeInteger(d.N)
        for v in d.tu:
            pw.writeReal(v)
        for v in d.tv:
            pw.writeReal(v)
        for p in d.patches:
            for v in p.coeff_x:
                pw.writeReal(v)
            for v in p.coeff_y:
                pw.writeReal(v)
            for v in p.coeff_z:
                pw.writeReal(v)
    registerEntity(114, _parse_114, _write_114)

    def _parse_116(tok, form):
        return obj({"coords": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "display_symbol": tok.nextPointer(0)})
    def _write_116(d, pw, form):
        pw.writeReal(d.coords[0])
        pw.writeReal(d.coords[1])
        pw.writeReal(d.coords[2])
        pw.writePointer(d.display_symbol or 0)
    registerEntity(116, _parse_116, _write_116)

    def _parse_118(tok, form):
        return obj({"de1": tok.nextPointer(0), "de2": tok.nextPointer(0), "dirflg": tok.nextInteger(0), "devflg": tok.nextInteger(0)})
    def _write_118(d, pw, form):
        pw.writePointer(d.de1)
        pw.writePointer(d.de2)
        pw.writeInteger(d.dirflg or 0)
        pw.writeInteger(d.devflg or 0)
    registerEntity(118, _parse_118, _write_118)

    def _parse_120(tok, form):
        return obj({"l": tok.nextPointer(0), "c": tok.nextPointer(0), "sa": tok.nextReal(0), "ta": tok.nextReal(0)})
    def _write_120(d, pw, form):
        pw.writePointer(d.l)
        pw.writePointer(d.c)
        pw.writeReal(d.sa)
        pw.writeReal(d.ta)
    registerEntity(120, _parse_120, _write_120)

    def _parse_122(tok, form):
        return obj({"de": tok.nextPointer(0), "terminate_point": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_122(d, pw, form):
        pw.writePointer(d.de)
        pw.writeReal(d.terminate_point[0])
        pw.writeReal(d.terminate_point[1])
        pw.writeReal(d.terminate_point[2])
    registerEntity(122, _parse_122, _write_122)

    def _parse_123(tok, form):
        return obj({"x": tok.nextReal(0), "y": tok.nextReal(0), "z": tok.nextReal(0)})
    def _write_123(d, pw, form):
        pw.writeReal(d.x)
        pw.writeReal(d.y)
        pw.writeReal(d.z)
    registerEntity(123, _parse_123, _write_123)

    def _parse_124(tok, form):
        r00 = tok.nextReal(0)
        r01 = tok.nextReal(0)
        r02 = tok.nextReal(0)
        t0 = tok.nextReal(0)
        r10 = tok.nextReal(0)
        r11 = tok.nextReal(0)
        r12 = tok.nextReal(0)
        t1 = tok.nextReal(0)
        r20 = tok.nextReal(0)
        r21 = tok.nextReal(0)
        r22 = tok.nextReal(0)
        t2 = tok.nextReal(0)
        return obj({"rotation": [[r00, r01, r02], [r10, r11, r12], [r20, r21, r22]], "translation": [t0, t1, t2]})
    def _write_124(d, pw, form):
        r = d.rotation
        t = d.translation
        pw.writeReal(r[0][0])
        pw.writeReal(r[0][1])
        pw.writeReal(r[0][2])
        pw.writeReal(t[0])
        pw.writeReal(r[1][0])
        pw.writeReal(r[1][1])
        pw.writeReal(r[1][2])
        pw.writeReal(t[1])
        pw.writeReal(r[2][0])
        pw.writeReal(r[2][1])
        pw.writeReal(r[2][2])
        pw.writeReal(t[2])
    registerEntity(124, _parse_124, _write_124)

    def _parse_125(tok, form):
        return obj({"x": tok.nextReal(0), "y": tok.nextReal(0), "dim1": tok.nextReal(0), "dim2": tok.nextReal(0), "rot": tok.nextReal(0), "de": tok.nextPointer(0)})
    def _write_125(d, pw, form):
        pw.writeReal(d.x)
        pw.writeReal(d.y)
        pw.writeReal(d.dim1 or 0)
        pw.writeReal(d.dim2 or 0)
        pw.writeReal(d.rot or 0)
        pw.writePointer(d.de or 0)
    registerEntity(125, _parse_125, _write_125)

    def _parse_126(tok, form):
        K = tok.nextInteger(0)
        M = tok.nextInteger(0)
        prop1 = tok.nextInteger(0)
        prop2 = tok.nextInteger(0)
        prop3 = tok.nextInteger(0)
        prop4 = tok.nextInteger(0)
        N = 1 + K - M
        A = N + 2 * M
        knots = []
        for i in range(0, (A) + 1):
            knots.append(tok.nextReal(0))
        weights = []
        for i in range(0, (K) + 1):
            weights.append(tok.nextReal(0))
        control_points = []
        for i in range(0, (K) + 1):
            control_points.append([tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)])
        v0 = tok.nextReal(0)
        v1 = tok.nextReal(0)
        plane_normal = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]
        return obj({"K": K, "M": M, "prop1": prop1, "prop2": prop2, "prop3": prop3, "prop4": prop4, "knots": knots, "weights": weights, "control_points": control_points, "v0": v0, "v1": v1, "plane_normal": plane_normal})
    def _write_126(d, pw, form):
        pw.writeInteger(d.K)
        pw.writeInteger(d.M)
        pw.writeInteger(d.prop1)
        pw.writeInteger(d.prop2)
        pw.writeInteger(d.prop3)
        pw.writeInteger(d.prop4)
        for v in d.knots:
            pw.writeReal(v)
        for v in d.weights:
            pw.writeReal(v)
        for p in d.control_points:
            pw.writeReal(p[0])
            pw.writeReal(p[1])
            pw.writeReal(p[2])
        pw.writeReal(d.v0)
        pw.writeReal(d.v1)
        pw.writeReal(d.plane_normal[0])
        pw.writeReal(d.plane_normal[1])
        pw.writeReal(d.plane_normal[2])
    registerEntity(126, _parse_126, _write_126)

    def _parse_128(tok, form):
        K1 = tok.nextInteger(0)
        K2 = tok.nextInteger(0)
        M1 = tok.nextInteger(0)
        M2 = tok.nextInteger(0)
        prop1 = tok.nextInteger(0)
        prop2 = tok.nextInteger(0)
        prop3 = tok.nextInteger(0)
        prop4 = tok.nextInteger(0)
        prop5 = tok.nextInteger(0)
        N1 = 1 + K1 - M1
        N2 = 1 + K2 - M2
        A = N1 + 2 * M1
        B = N2 + 2 * M2
        C = (K1 + 1) * (K2 + 1)
        knots_u = []
        for i in range(0, (A) + 1):
            knots_u.append(tok.nextReal(0))
        knots_v = []
        for i in range(0, (B) + 1):
            knots_v.append(tok.nextReal(0))
        weights = []
        for i in range(0, C):
            weights.append(tok.nextReal(0))
        control_points = []
        for i in range(0, C):
            control_points.append([tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)])
        return obj({"K1": K1, "K2": K2, "M1": M1, "M2": M2, "prop1": prop1, "prop2": prop2, "prop3": prop3, "prop4": prop4, "prop5": prop5, "knots_u": knots_u, "knots_v": knots_v, "weights": weights, "control_points": control_points, "u0": tok.nextReal(0), "u1": tok.nextReal(0), "v0": tok.nextReal(0), "v1": tok.nextReal(0)})
    def _write_128(d, pw, form):
        pw.writeInteger(d.K1)
        pw.writeInteger(d.K2)
        pw.writeInteger(d.M1)
        pw.writeInteger(d.M2)
        pw.writeInteger(d.prop1)
        pw.writeInteger(d.prop2)
        pw.writeInteger(d.prop3)
        pw.writeInteger(d.prop4)
        pw.writeInteger(d.prop5)
        for v in d.knots_u:
            pw.writeReal(v)
        for v in d.knots_v:
            pw.writeReal(v)
        for w in d.weights:
            pw.writeReal(w)
        for p in d.control_points:
            pw.writeReal(p[0])
            pw.writeReal(p[1])
            pw.writeReal(p[2])
        pw.writeReal(d.u0)
        pw.writeReal(d.u1)
        pw.writeReal(d.v0)
        pw.writeReal(d.v1)
    registerEntity(128, _parse_128, _write_128)

    def _parse_130(tok, form):
        return obj({"de1": tok.nextPointer(0), "flag": tok.nextInteger(0), "de2": tok.nextPointer(0), "ndim": tok.nextInteger(0), "ptype": tok.nextInteger(0), "d1": tok.nextReal(0), "td1": tok.nextReal(0), "d2": tok.nextReal(0), "td2": tok.nextReal(0), "vx": tok.nextReal(0), "vy": tok.nextReal(0), "vz": tok.nextReal(0), "tt1": tok.nextReal(0), "tt2": tok.nextReal(0)})
    def _write_130(d, pw, form):
        pw.writePointer(d.de1)
        pw.writeInteger(d.flag)
        pw.writePointer(d.de2 or 0)
        pw.writeInteger(d.ndim or 0)
        pw.writeInteger(d.ptype or 0)
        pw.writeReal(d.d1 or 0)
        pw.writeReal(d.td1 or 0)
        pw.writeReal(d.d2 or 0)
        pw.writeReal(d.td2 or 0)
        pw.writeReal(d.vx)
        pw.writeReal(d.vy)
        pw.writeReal(d.vz)
        pw.writeReal(d.tt1)
        pw.writeReal(d.tt2)
    registerEntity(130, _parse_130, _write_130)

    def _parse_132(tok, form):
        return obj({"location": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "display_symbol": tok.nextPointer(0), "tf": tok.nextInteger(0), "ff": tok.nextInteger(0), "cid": tok.nextString(""), "pttcid": tok.nextPointer(0), "cfn": tok.nextString(""), "pttcfn": tok.nextPointer(0), "cpid": tok.nextInteger(0), "fc": tok.nextInteger(0), "sf": tok.nextInteger(0), "psfi": tok.nextPointer(0)})
    def _write_132(d, pw, form):
        pw.writeReal(d.location[0])
        pw.writeReal(d.location[1])
        pw.writeReal(d.location[2])
        pw.writePointer(d.display_symbol or 0)
        pw.writeInteger(d.tf or 0)
        pw.writeInteger(d.ff or 0)
        pw.writeString(d.cid or "")
        pw.writePointer(d.pttcid or 0)
        pw.writeString(d.cfn or "")
        pw.writePointer(d.pttcfn or 0)
        pw.writeInteger(d.cpid or 0)
        pw.writeInteger(d.fc or 0)
        pw.writeInteger(d.sf or 0)
        pw.writePointer(d.psfi or 0)
    registerEntity(132, _parse_132, _write_132)

    def _parse_134(tok, form):
        return obj({"x": tok.nextReal(0), "y": tok.nextReal(0), "z": tok.nextReal(0), "ndcsp": tok.nextPointer(0)})
    def _write_134(d, pw, form):
        pw.writeReal(d.x)
        pw.writeReal(d.y)
        pw.writeReal(d.z)
        pw.writePointer(d.ndcsp or 0)
    registerEntity(134, _parse_134, _write_134)

    def _parse_136(tok, form):
        itop = tok.nextInteger(0)
        n = tok.nextInteger(0)
        nodes = []
        for i in range(0, n):
            nodes.append(tok.nextPointer(0))
        etyp = tok.nextString("")
        return obj({"itop": itop, "n": n, "nodes": nodes, "etyp": etyp})
    def _write_136(d, pw, form):
        pw.writeInteger(d.itop)
        pw.writeInteger(len(d.nodes))
        for p in d.nodes:
            pw.writePointer(p)
        pw.writeString(d.etyp or "")
    registerEntity(136, _parse_136, _write_136)

    def _parse_138(tok, form):
        nc = tok.nextInteger(0)
        gp = []
        for i in range(0, nc):
            gp.append(tok.nextPointer(0))
        nn = tok.nextInteger(0)
        nodes = []
        for i in range(0, nn):
            node_id = tok.nextInteger(0)
            np = tok.nextPointer(0)
            cases = []
            for j in range(0, nc):
                cases.append(obj({"x": tok.nextReal(0), "y": tok.nextReal(0), "z": tok.nextReal(0), "rx": tok.nextReal(0), "ry": tok.nextReal(0), "rz": tok.nextReal(0)}))
            nodes.append(obj({"node_id": node_id, "np": np, "cases": cases}))
        return obj({"nc": nc, "gp": gp, "nn": nn, "nodes": nodes})
    def _write_138(d, pw, form):
        pw.writeInteger(d.nc)
        for p in d.gp:
            pw.writePointer(p)
        pw.writeInteger(d.nn)
        for nd in d.nodes:
            pw.writeInteger(nd.node_id)
            pw.writePointer(nd.np)
            for c in nd.cases:
                pw.writeReal(c.x)
                pw.writeReal(c.y)
                pw.writeReal(c.z)
                pw.writeReal(c.rx)
                pw.writeReal(c.ry)
                pw.writeReal(c.rz)
    registerEntity(138, _parse_138, _write_138)

    def _parse_140(tok, form):
        return obj({"nx": tok.nextReal(0), "ny": tok.nextReal(0), "nz": tok.nextReal(0), "d": tok.nextReal(0), "de": tok.nextPointer(0)})
    def _write_140(d, pw, form):
        pw.writeReal(d.nx)
        pw.writeReal(d.ny)
        pw.writeReal(d.nz)
        pw.writeReal(d.d)
        pw.writePointer(d.de)
    registerEntity(140, _parse_140, _write_140)

    def _parse_141(tok, form):
        type = tok.nextInteger(0)
        pref = tok.nextInteger(0)
        sptr = tok.nextPointer(0)
        n = tok.nextInteger(0)
        curves = []
        for i in range(0, n):
            crvpt = tok.nextPointer(0)
            sense = tok.nextInteger(0)
            k = tok.nextInteger(0)
            pscpt = []
            for j in range(0, k):
                pscpt.append(tok.nextPointer(0))
            curves.append(obj({"crvpt": crvpt, "sense": sense, "k": k, "pscpt": pscpt}))
        return obj({"type": type, "pref": pref, "sptr": sptr, "n": n, "curves": curves})
    def _write_141(d, pw, form):
        pw.writeInteger(d.type)
        pw.writeInteger(d.pref)
        pw.writePointer(d.sptr)
        pw.writeInteger(len(d.curves))
        for c in d.curves:
            pw.writePointer(c.crvpt)
            pw.writeInteger(c.sense)
            pw.writeInteger(len(c.pscpt))
            for p in c.pscpt:
                pw.writePointer(p)
    registerEntity(141, _parse_141, _write_141)

    def _parse_142(tok, form):
        return obj({"crtn": tok.nextInteger(0), "sptr": tok.nextPointer(0), "bptr": tok.nextPointer(0), "cptr": tok.nextPointer(0), "pref": tok.nextInteger(0)})
    def _write_142(d, pw, form):
        pw.writeInteger(d.crtn)
        pw.writePointer(d.sptr)
        pw.writePointer(d.bptr)
        pw.writePointer(d.cptr)
        pw.writeInteger(d.pref)
    registerEntity(142, _parse_142, _write_142)

    def _parse_143(tok, form):
        type = tok.nextInteger(0)
        sptr = tok.nextPointer(0)
        n = tok.nextInteger(0)
        bdpt = []
        for i in range(0, n):
            bdpt.append(tok.nextPointer(0))
        return obj({"type": type, "sptr": sptr, "n": n, "bdpt": bdpt})
    def _write_143(d, pw, form):
        pw.writeInteger(d.type)
        pw.writePointer(d.sptr)
        pw.writeInteger(len(d.bdpt))
        for p in d.bdpt:
            pw.writePointer(p)
    registerEntity(143, _parse_143, _write_143)

    def _parse_144(tok, form):
        pts = tok.nextPointer(0)
        n1 = tok.nextInteger(0)
        n2 = tok.nextInteger(0)
        pto = tok.nextPointer(0)
        pti = []
        for i in range(0, n2):
            pti.append(tok.nextPointer(0))
        return obj({"pts": pts, "n1": n1, "n2": n2, "pto": pto, "pti": pti})
    def _write_144(d, pw, form):
        pw.writePointer(d.pts)
        pw.writeInteger(d.n1)
        pw.writeInteger(d.n2)
        pw.writePointer(d.pto)
        for p in d.pti:
            pw.writePointer(p)
    registerEntity(144, _parse_144, _write_144)

    def _parse_146(tok, form):
        gnote = tok.nextPointer(0)
        scn = tok.nextInteger(0)
        time = tok.nextReal(0)
        nv = tok.nextInteger(0)
        nn = tok.nextInteger(0)
        nodes = []
        for i in range(0, nn):
            node_id = tok.nextInteger(0)
            np = tok.nextPointer(0)
            values = []
            for j in range(0, nv):
                values.append(tok.nextReal(0))
            nodes.append(obj({"node_id": node_id, "np": np, "values": values}))
        return obj({"gnote": gnote, "scn": scn, "time": time, "nv": nv, "nn": nn, "nodes": nodes})
    def _write_146(d, pw, form):
        pw.writePointer(d.gnote)
        pw.writeInteger(d.scn)
        pw.writeReal(d.time)
        pw.writeInteger(d.nv)
        pw.writeInteger(d.nn)
        for n in d.nodes:
            pw.writeInteger(n.node_id)
            pw.writePointer(n.np)
            for v in n["values"]:
                pw.writeReal(v)
    registerEntity(146, _parse_146, _write_146)

    def _parse_148(tok, form):
        gnote = tok.nextPointer(0)
        scn = tok.nextInteger(0)
        time = tok.nextReal(0)
        nv = tok.nextInteger(0)
        rrf = tok.nextInteger(0)
        ne = tok.nextInteger(0)
        elements = []
        for i in range(0, ne):
            en = tok.nextInteger(0)
            ep = tok.nextPointer(0)
            itop = tok.nextInteger(0)
            nl = tok.nextInteger(0)
            dlf = tok.nextInteger(0)
            nrl = tok.nextInteger(0)
            rdrl = []
            for j in range(0, nrl):
                rdrl.append(tok.nextInteger(0))
            numv = tok.nextInteger(0)
            values = []
            for j in range(0, numv):
                values.append(tok.nextReal(0))
            elements.append(obj({"en": en, "ep": ep, "itop": itop, "nl": nl, "dlf": dlf, "nrl": nrl, "rdrl": rdrl, "numv": numv, "values": values}))
        return obj({"gnote": gnote, "scn": scn, "time": time, "nv": nv, "rrf": rrf, "ne": ne, "elements": elements})
    def _write_148(d, pw, form):
        pw.writePointer(d.gnote)
        pw.writeInteger(d.scn)
        pw.writeReal(d.time)
        pw.writeInteger(d.nv)
        pw.writeInteger(d.rrf)
        pw.writeInteger(d.ne)
        for el in d.elements:
            pw.writeInteger(el.en)
            pw.writePointer(el.ep)
            pw.writeInteger(el.itop)
            pw.writeInteger(el.nl)
            pw.writeInteger(el.dlf)
            pw.writeInteger(el.nrl)
            for r in el.rdrl:
                pw.writeInteger(r)
            pw.writeInteger(el.numv)
            for v in el["values"]:
                pw.writeReal(v)
    registerEntity(148, _parse_148, _write_148)

    def _parse_150(tok, form):
        return obj({"lx": tok.nextReal(0), "ly": tok.nextReal(0), "lz": tok.nextReal(0), "corner": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "x_axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "z_axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_150(d, pw, form):
        pw.writeReal(d.lx)
        pw.writeReal(d.ly)
        pw.writeReal(d.lz)
        pw.writeReal(d.corner[0])
        pw.writeReal(d.corner[1])
        pw.writeReal(d.corner[2])
        pw.writeReal(d.x_axis[0])
        pw.writeReal(d.x_axis[1])
        pw.writeReal(d.x_axis[2])
        pw.writeReal(d.z_axis[0])
        pw.writeReal(d.z_axis[1])
        pw.writeReal(d.z_axis[2])
    registerEntity(150, _parse_150, _write_150)

    def _parse_152(tok, form):
        return obj({"lx": tok.nextReal(0), "ly": tok.nextReal(0), "lz": tok.nextReal(0), "ltx": tok.nextReal(0), "corner": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "x_axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "z_axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_152(d, pw, form):
        pw.writeReal(d.lx)
        pw.writeReal(d.ly)
        pw.writeReal(d.lz)
        pw.writeReal(d.ltx)
        pw.writeReal(d.corner[0])
        pw.writeReal(d.corner[1])
        pw.writeReal(d.corner[2])
        pw.writeReal(d.x_axis[0])
        pw.writeReal(d.x_axis[1])
        pw.writeReal(d.x_axis[2])
        pw.writeReal(d.z_axis[0])
        pw.writeReal(d.z_axis[1])
        pw.writeReal(d.z_axis[2])
    registerEntity(152, _parse_152, _write_152)

    def _parse_154(tok, form):
        return obj({"h": tok.nextReal(0), "r": tok.nextReal(0), "face_center": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_154(d, pw, form):
        pw.writeReal(d.h)
        pw.writeReal(d.r)
        pw.writeReal(d.face_center[0])
        pw.writeReal(d.face_center[1])
        pw.writeReal(d.face_center[2])
        pw.writeReal(d.axis[0])
        pw.writeReal(d.axis[1])
        pw.writeReal(d.axis[2])
    registerEntity(154, _parse_154, _write_154)

    def _parse_156(tok, form):
        return obj({"h": tok.nextReal(0), "r1": tok.nextReal(0), "r2": tok.nextReal(0), "face_center": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_156(d, pw, form):
        pw.writeReal(d.h)
        pw.writeReal(d.r1)
        pw.writeReal(d.r2)
        pw.writeReal(d.face_center[0])
        pw.writeReal(d.face_center[1])
        pw.writeReal(d.face_center[2])
        pw.writeReal(d.axis[0])
        pw.writeReal(d.axis[1])
        pw.writeReal(d.axis[2])
    registerEntity(156, _parse_156, _write_156)

    def _parse_158(tok, form):
        return obj({"radius": tok.nextReal(0), "center": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_158(d, pw, form):
        pw.writeReal(d.radius)
        pw.writeReal(d.center[0])
        pw.writeReal(d.center[1])
        pw.writeReal(d.center[2])
    registerEntity(158, _parse_158, _write_158)

    def _parse_160(tok, form):
        return obj({"r1": tok.nextReal(0), "r2": tok.nextReal(0), "center": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_160(d, pw, form):
        pw.writeReal(d.r1)
        pw.writeReal(d.r2)
        pw.writeReal(d.center[0])
        pw.writeReal(d.center[1])
        pw.writeReal(d.center[2])
        pw.writeReal(d.axis[0])
        pw.writeReal(d.axis[1])
        pw.writeReal(d.axis[2])
    registerEntity(160, _parse_160, _write_160)

    def _parse_162(tok, form):
        return obj({"ptr": tok.nextPointer(0), "f": tok.nextReal(0), "axis_point": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "axis_dir": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_162(d, pw, form):
        pw.writePointer(d.ptr)
        pw.writeReal(d.f)
        pw.writeReal(d.axis_point[0])
        pw.writeReal(d.axis_point[1])
        pw.writeReal(d.axis_point[2])
        pw.writeReal(d.axis_dir[0])
        pw.writeReal(d.axis_dir[1])
        pw.writeReal(d.axis_dir[2])
    registerEntity(162, _parse_162, _write_162)

    def _parse_164(tok, form):
        return obj({"ptr": tok.nextPointer(0), "length": tok.nextReal(0), "direction": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_164(d, pw, form):
        pw.writePointer(d.ptr)
        pw.writeReal(d.length)
        pw.writeReal(d.direction[0])
        pw.writeReal(d.direction[1])
        pw.writeReal(d.direction[2])
    registerEntity(164, _parse_164, _write_164)

    def _parse_168(tok, form):
        return obj({"lx": tok.nextReal(0), "ly": tok.nextReal(0), "lz": tok.nextReal(0), "center": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "x_axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "z_axis": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_168(d, pw, form):
        pw.writeReal(d.lx)
        pw.writeReal(d.ly)
        pw.writeReal(d.lz)
        pw.writeReal(d.center[0])
        pw.writeReal(d.center[1])
        pw.writeReal(d.center[2])
        pw.writeReal(d.x_axis[0])
        pw.writeReal(d.x_axis[1])
        pw.writeReal(d.x_axis[2])
        pw.writeReal(d.z_axis[0])
        pw.writeReal(d.z_axis[1])
        pw.writeReal(d.z_axis[2])
    registerEntity(168, _parse_168, _write_168)

    def _parse_180(tok, form):
        n = tok.nextInteger(0)
        entries = []
        for i in range(0, n):
            entries.append(tok.nextInteger(0))
        return obj({"n": n, "entries": entries})
    def _write_180(d, pw, form):
        pw.writeInteger(len(d.entries))
        for v in d.entries:
            pw.writeInteger(v)
    registerEntity(180, _parse_180, _write_180)

    def _parse_182(tok, form):
        return obj({"btree": tok.nextPointer(0), "sel_point": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]})
    def _write_182(d, pw, form):
        pw.writePointer(d.btree)
        pw.writeReal(d.sel_point[0])
        pw.writeReal(d.sel_point[1])
        pw.writeReal(d.sel_point[2])
    registerEntity(182, _parse_182, _write_182)

    def _parse_184(tok, form):
        n = tok.nextInteger(0)
        items = []
        for i in range(0, n):
            items.append(tok.nextPointer(0))
        transforms = []
        for i in range(0, n):
            transforms.append(tok.nextPointer(0))
        return obj({"n": n, "items": items, "transforms": transforms})
    def _write_184(d, pw, form):
        pw.writeInteger(len(d["items"]))
        for p in d["items"]:
            pw.writePointer(p)
        for p in d.transforms:
            pw.writePointer(p)
    registerEntity(184, _parse_184, _write_184)

    def _parse_186(tok, form):
        shell = tok.nextPointer(0)
        sof = tok.nextLogical(False)
        n = tok.nextInteger(0)
        voids = []
        for i in range(0, n):
            voids.append(obj({"shell": tok.nextPointer(0), "orientation": tok.nextLogical(False)}))
        return obj({"shell": shell, "sof": sof, "n": n, "voids": voids})
    def _write_186(d, pw, form):
        pw.writePointer(d.shell)
        pw.writeLogical(d.sof)
        pw.writeInteger(len(d.voids))
        for v in d.voids:
            pw.writePointer(v.shell)
            pw.writeLogical(v.orientation)
    registerEntity(186, _parse_186, _write_186)

    def _parse_190(tok, form):
        deloc = tok.nextPointer(0)
        denrml = tok.nextPointer(0)
        derefd = tok.nextPointer(0) if form == 1 else 0
        return obj({"deloc": deloc, "denrml": denrml, "derefd": derefd})
    def _write_190(d, pw, form):
        pw.writePointer(d.deloc)
        pw.writePointer(d.denrml)
        if form == 1:
            pw.writePointer(d.derefd or 0)
    registerEntity(190, _parse_190, _write_190)

    def _parse_192(tok, form):
        deloc = tok.nextPointer(0)
        deaxis = tok.nextPointer(0)
        radius = tok.nextReal(0)
        derefd = tok.nextPointer(0) if form == 1 else 0
        return obj({"deloc": deloc, "deaxis": deaxis, "radius": radius, "derefd": derefd})
    def _write_192(d, pw, form):
        pw.writePointer(d.deloc)
        pw.writePointer(d.deaxis)
        pw.writeReal(d.radius)
        if form == 1:
            pw.writePointer(d.derefd or 0)
    registerEntity(192, _parse_192, _write_192)

    def _parse_194(tok, form):
        deloc = tok.nextPointer(0)
        deaxis = tok.nextPointer(0)
        radius = tok.nextReal(0)
        sangle = tok.nextReal(0)
        derefd = tok.nextPointer(0) if form == 1 else 0
        return obj({"deloc": deloc, "deaxis": deaxis, "radius": radius, "sangle": sangle, "derefd": derefd})
    def _write_194(d, pw, form):
        pw.writePointer(d.deloc)
        pw.writePointer(d.deaxis)
        pw.writeReal(d.radius)
        pw.writeReal(d.sangle)
        if form == 1:
            pw.writePointer(d.derefd or 0)
    registerEntity(194, _parse_194, _write_194)

    def _parse_196(tok, form):
        deloc = tok.nextPointer(0)
        radius = tok.nextReal(0)
        deaxis = tok.nextPointer(0) if form == 1 else 0
        derefd = tok.nextPointer(0) if form == 1 else 0
        return obj({"deloc": deloc, "radius": radius, "deaxis": deaxis, "derefd": derefd})
    def _write_196(d, pw, form):
        pw.writePointer(d.deloc)
        pw.writeReal(d.radius)
        if form == 1:
            pw.writePointer(d.deaxis or 0)
            pw.writePointer(d.derefd or 0)
    registerEntity(196, _parse_196, _write_196)

    def _parse_198(tok, form):
        deloc = tok.nextPointer(0)
        deaxis = tok.nextPointer(0)
        majrad = tok.nextReal(0)
        minrad = tok.nextReal(0)
        derefd = tok.nextPointer(0) if form == 1 else 0
        return obj({"deloc": deloc, "deaxis": deaxis, "majrad": majrad, "minrad": minrad, "derefd": derefd})
    def _write_198(d, pw, form):
        pw.writePointer(d.deloc)
        pw.writePointer(d.deaxis)
        pw.writeReal(d.majrad)
        pw.writeReal(d.minrad)
        if form == 1:
            pw.writePointer(d.derefd or 0)
    registerEntity(198, _parse_198, _write_198)

    def _parse_202(tok, form):
        return obj({"denote": tok.nextPointer(0), "dewit1": tok.nextPointer(0), "dewit2": tok.nextPointer(0), "xt": tok.nextReal(0), "yt": tok.nextReal(0), "radius": tok.nextReal(0), "dearrw1": tok.nextPointer(0), "dearrw2": tok.nextPointer(0)})
    def _write_202(d, pw, form):
        pw.writePointer(d.denote)
        pw.writePointer(d.dewit1)
        pw.writePointer(d.dewit2)
        pw.writeReal(d.xt)
        pw.writeReal(d.yt)
        pw.writeReal(d.radius)
        pw.writePointer(d.dearrw1)
        pw.writePointer(d.dearrw2)
    registerEntity(202, _parse_202, _write_202)

    def _parse_204(tok, form):
        return obj({"denote": tok.nextPointer(0), "decurv1": tok.nextPointer(0), "decurv2": tok.nextPointer(0), "dearr1": tok.nextPointer(0), "dearr2": tok.nextPointer(0), "dewit1": tok.nextPointer(0), "dewit2": tok.nextPointer(0)})
    def _write_204(d, pw, form):
        pw.writePointer(d.denote)
        pw.writePointer(d.decurv1)
        pw.writePointer(d.decurv2)
        pw.writePointer(d.dearr1)
        pw.writePointer(d.dearr2)
        pw.writePointer(d.dewit1)
        pw.writePointer(d.dewit2)
    registerEntity(204, _parse_204, _write_204)

    def _parse_206(tok, form):
        return obj({"denote": tok.nextPointer(0), "dearrw1": tok.nextPointer(0), "dearrw2": tok.nextPointer(0), "xt": tok.nextReal(0), "yt": tok.nextReal(0)})
    def _write_206(d, pw, form):
        pw.writePointer(d.denote)
        pw.writePointer(d.dearrw1)
        pw.writePointer(d.dearrw2)
        pw.writeReal(d.xt)
        pw.writeReal(d.yt)
    registerEntity(206, _parse_206, _write_206)

    def _parse_208(tok, form):
        xt = tok.nextReal(0)
        yt = tok.nextReal(0)
        zt = tok.nextReal(0)
        angle = tok.nextReal(0)
        denote = tok.nextPointer(0)
        n = tok.nextInteger(0)
        leaders = []
        for i in range(0, n):
            leaders.append(tok.nextPointer(0))
        return obj({"xt": xt, "yt": yt, "zt": zt, "angle": angle, "denote": denote, "n": n, "leaders": leaders})
    def _write_208(d, pw, form):
        pw.writeReal(d.xt)
        pw.writeReal(d.yt)
        pw.writeReal(d.zt)
        pw.writeReal(d.angle)
        pw.writePointer(d.denote)
        pw.writeInteger(len(d.leaders))
        for p in d.leaders:
            pw.writePointer(p)
    registerEntity(208, _parse_208, _write_208)

    def _parse_210(tok, form):
        denote = tok.nextPointer(0)
        n = tok.nextInteger(0)
        leaders = []
        for i in range(0, n):
            leaders.append(tok.nextPointer(0))
        return obj({"denote": denote, "n": n, "leaders": leaders})
    def _write_210(d, pw, form):
        pw.writePointer(d.denote)
        pw.writeInteger(len(d.leaders))
        for p in d.leaders:
            pw.writePointer(p)
    registerEntity(210, _parse_210, _write_210)

    def _parse_212(tok, form):
        ns = tok.nextInteger(0)
        strings = []
        for i in range(0, ns):
            strings.append(obj({"nc": tok.nextInteger(0), "wc": tok.nextReal(0), "hc": tok.nextReal(0), "fc": tok.nextInteger(0), "slant": tok.nextReal(0), "angle": tok.nextReal(0), "mirror": tok.nextInteger(0), "vh": tok.nextInteger(0), "start": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "text": tok.nextString("")}))
        return obj({"ns": ns, "strings": strings})
    def _write_212(d, pw, form):
        pw.writeInteger(len(d.strings))
        for s in d.strings:
            pw.writeInteger(s.nc)
            pw.writeReal(s.wc)
            pw.writeReal(s.hc)
            pw.writeInteger(s.fc)
            pw.writeReal(s.slant)
            pw.writeReal(s.angle)
            pw.writeInteger(s.mirror)
            pw.writeInteger(s.vh)
            pw.writeReal(s.start[0])
            pw.writeReal(s.start[1])
            pw.writeReal(s.start[2])
            pw.writeString(s.text or "")
    registerEntity(212, _parse_212, _write_212)

    def _parse_213(tok, form):
        d = obj({"txtcw": tok.nextReal(0), "txtch": tok.nextReal(0), "justcd": tok.nextInteger(0), "txtcx": tok.nextReal(0), "txtcy": tok.nextReal(0), "txtcz": tok.nextReal(0), "txtag": tok.nextReal(0), "baselx": tok.nextReal(0), "basely": tok.nextReal(0), "baselz": tok.nextReal(0), "nils": tok.nextReal(0)})
        ns = tok.nextInteger(0)
        strings = []
        for i in range(0, ns):
            strings.append(obj({"fixvar": tok.nextInteger(0), "chrwid": tok.nextReal(0), "chrhgt": tok.nextReal(0), "cspace": tok.nextReal(0), "lspace": tok.nextReal(0), "font": tok.nextInteger(0), "chrang": tok.nextReal(0), "cctext": tok.nextString(""), "nc": tok.nextInteger(0), "wt": tok.nextReal(0), "ht": tok.nextReal(0), "chrset": tok.nextInteger(0), "sl": tok.nextReal(0), "a": tok.nextReal(0), "m": tok.nextInteger(0), "vh": tok.nextInteger(0), "xs": tok.nextReal(0), "ys": tok.nextReal(0), "zs": tok.nextReal(0), "text": tok.nextString("")}))
        d.ns = ns
        d.strings = strings
        return d
    def _write_213(d, pw, form):
        pw.writeReal(d.txtcw)
        pw.writeReal(d.txtch)
        pw.writeInteger(d.justcd)
        pw.writeReal(d.txtcx)
        pw.writeReal(d.txtcy)
        pw.writeReal(d.txtcz)
        pw.writeReal(d.txtag)
        pw.writeReal(d.baselx)
        pw.writeReal(d.basely)
        pw.writeReal(d.baselz)
        pw.writeReal(d.nils)
        pw.writeInteger(len(d.strings))
        for s in d.strings:
            pw.writeInteger(s.fixvar)
            pw.writeReal(s.chrwid)
            pw.writeReal(s.chrhgt)
            pw.writeReal(s.cspace)
            pw.writeReal(s.lspace)
            pw.writeInteger(s.font)
            pw.writeReal(s.chrang)
            pw.writeString(s.cctext or "")
            pw.writeInteger(s.nc)
            pw.writeReal(s.wt)
            pw.writeReal(s.ht)
            pw.writeInteger(s.chrset)
            pw.writeReal(s.sl)
            pw.writeReal(s.a)
            pw.writeInteger(s.m)
            pw.writeInteger(s.vh)
            pw.writeReal(s.xs)
            pw.writeReal(s.ys)
            pw.writeReal(s.zs)
            pw.writeString(s.text or "")
    registerEntity(213, _parse_213, _write_213)

    def _parse_214(tok, form):
        n = tok.nextInteger(0)
        ad1 = tok.nextReal(0)
        ad2 = tok.nextReal(0)
        zt = tok.nextReal(0)
        xh = tok.nextReal(0)
        yh = tok.nextReal(0)
        segments = []
        for i in range(0, n):
            segments.append(obj({"x": tok.nextReal(0), "y": tok.nextReal(0)}))
        return obj({"n": n, "ad1": ad1, "ad2": ad2, "zt": zt, "xh": xh, "yh": yh, "segments": segments})
    def _write_214(d, pw, form):
        pw.writeInteger(len(d.segments))
        pw.writeReal(d.ad1)
        pw.writeReal(d.ad2)
        pw.writeReal(d.zt)
        pw.writeReal(d.xh)
        pw.writeReal(d.yh)
        for s in d.segments:
            pw.writeReal(s.x)
            pw.writeReal(s.y)
    registerEntity(214, _parse_214, _write_214)

    def _parse_216(tok, form):
        return obj({"denote": tok.nextPointer(0), "dearrw1": tok.nextPointer(0), "dearrw2": tok.nextPointer(0), "dewit1": tok.nextPointer(0), "dewit2": tok.nextPointer(0), "xt": tok.nextReal(0), "yt": tok.nextReal(0)})
    def _write_216(d, pw, form):
        pw.writePointer(d.denote)
        pw.writePointer(d.dearrw1)
        pw.writePointer(d.dearrw2)
        pw.writePointer(d.dewit1)
        pw.writePointer(d.dewit2)
        pw.writeReal(d.xt)
        pw.writeReal(d.yt)
    registerEntity(216, _parse_216, _write_216)

    def _parse_218(tok, form):
        denote = tok.nextPointer(0)
        if form == 1:
            return obj({"form": form, "denote": denote, "dewit": 0, "deord": tok.nextPointer(0), "desupp": tok.nextPointer(0)})
        return obj({"form": form or 0, "denote": denote, "dewit": tok.nextPointer(0), "deord": 0, "desupp": 0})
    def _write_218(d, pw, form):
        pw.writePointer(d.denote)
        if form == 1:
            pw.writePointer(d.deord or 0)
            pw.writePointer(d.desupp or 0)
        else:
            pw.writePointer(d.dewit or 0)
    registerEntity(218, _parse_218, _write_218)

    def _parse_220(tok, form):
        return obj({"denote": tok.nextPointer(0), "dearrw": tok.nextPointer(0), "degeom": tok.nextPointer(0)})
    def _write_220(d, pw, form):
        pw.writePointer(d.denote)
        pw.writePointer(d.dearrw)
        pw.writePointer(d.degeom)
    registerEntity(220, _parse_220, _write_220)

    def _parse_222(tok, form):
        denote = tok.nextPointer(0)
        dearrw = tok.nextPointer(0)
        xt = tok.nextReal(0)
        yt = tok.nextReal(0)
        dearrw2 = tok.nextPointer(0) if form == 1 else 0
        return obj({"form": form or 0, "denote": denote, "dearrw": dearrw, "xt": xt, "yt": yt, "dearrw2": dearrw2})
    def _write_222(d, pw, form):
        pw.writePointer(d.denote)
        pw.writePointer(d.dearrw)
        pw.writeReal(d.xt)
        pw.writeReal(d.yt)
        if form == 1:
            pw.writePointer(d.dearrw2 or 0)
    registerEntity(222, _parse_222, _write_222)

    def _parse_228(tok, form):
        denote = tok.nextPointer(0)
        n = tok.nextInteger(0)
        geometries = []
        for i in range(0, n):
            geometries.append(tok.nextPointer(0))
        l = tok.nextInteger(0)
        leaders = []
        for i in range(0, l):
            leaders.append(tok.nextPointer(0))
        return obj({"denote": denote, "n": n, "geometries": geometries, "l": l, "leaders": leaders})
    def _write_228(d, pw, form):
        pw.writePointer(d.denote)
        pw.writeInteger(len(d.geometries))
        for p in d.geometries:
            pw.writePointer(p)
        pw.writeInteger(len(d.leaders))
        for p in d.leaders:
            pw.writePointer(p)
    registerEntity(228, _parse_228, _write_228)

    def _parse_230(tok, form):
        bndp = tok.nextPointer(0)
        patrn = tok.nextInteger(0)
        xt = tok.nextReal(0)
        yt = tok.nextReal(0)
        zt = tok.nextReal(0)
        dist = tok.nextReal(0)
        angle = tok.nextReal(0)
        n = tok.nextInteger(0)
        islands = []
        for i in range(0, n):
            islands.append(tok.nextPointer(0))
        return obj({"bndp": bndp, "patrn": patrn, "xt": xt, "yt": yt, "zt": zt, "dist": dist, "angle": angle, "n": n, "islands": islands})
    def _write_230(d, pw, form):
        pw.writePointer(d.bndp)
        pw.writeInteger(d.patrn)
        pw.writeReal(d.xt)
        pw.writeReal(d.yt)
        pw.writeReal(d.zt)
        pw.writeReal(d.dist)
        pw.writeReal(d.angle)
        pw.writeInteger(len(d.islands))
        for p in d.islands:
            pw.writePointer(p)
    registerEntity(230, _parse_230, _write_230)

    def _parse_302(tok, form):
        k = tok.nextInteger(0)
        classes = []
        for i in range(0, k):
            bp = tok.nextInteger(0)
            order = tok.nextInteger(0)
            n = tok.nextInteger(0)
            item_types = []
            for j in range(0, n):
                item_types.append(tok.nextInteger(0))
            classes.append(obj({"bp": bp, "order": order, "n": n, "item_types": item_types}))
        return obj({"k": k, "classes": classes})
    def _write_302(d, pw, form):
        pw.writeInteger(len(d.classes))
        for c in d.classes:
            pw.writeInteger(c.bp)
            pw.writeInteger(c.order)
            pw.writeInteger(len(c.item_types))
            for it in c.item_types:
                pw.writeInteger(it)
    registerEntity(302, _parse_302, _write_302)

    def _parse_304(tok, form):
        m = tok.nextInteger(0)
        if form == 1:
            return obj({"form": form, "m": m, "l1": tok.nextPointer(0), "l2": tok.nextReal(0), "l3": tok.nextReal(0), "segments": [], "bitmask": ""})
        segments = []
        for i in range(0, m):
            segments.append(tok.nextReal(0))
        bitmask = tok.nextString("")
        return obj({"form": form or 2, "m": m, "l1": 0, "l2": 0, "l3": 0, "segments": segments, "bitmask": bitmask})
    def _write_304(d, pw, form):
        pw.writeInteger(d.m)
        if form == 1:
            pw.writePointer(d.l1 or 0)
            pw.writeReal(d.l2 or 0)
            pw.writeReal(d.l3 or 0)
        else:
            for s in d.segments:
                pw.writeReal(s)
            pw.writeString(d.bitmask or "")
    registerEntity(304, _parse_304, _write_304)

    def _parse_308(tok, form):
        depth = tok.nextInteger(0)
        name = tok.nextString("")
        n = tok.nextInteger(0)
        entities = []
        for i in range(0, n):
            entities.append(tok.nextPointer(0))
        return obj({"depth": depth, "name": name, "n": n, "entities": entities})
    def _write_308(d, pw, form):
        pw.writeInteger(d.depth)
        pw.writeString(d.name or "")
        pw.writeInteger(len(d.entities))
        for p in d.entities:
            pw.writePointer(p)
    registerEntity(308, _parse_308, _write_308)

    def _parse_310(tok, form):
        fc = tok.nextInteger(0)
        fname = tok.nextString("")
        sf = tok.nextInteger(0)
        scale = tok.nextInteger(0)
        n = tok.nextInteger(0)
        characters = []
        for i in range(0, n):
            ac = tok.nextInteger(0)
            nx = tok.nextInteger(0)
            ny = tok.nextInteger(0)
            nm = tok.nextInteger(0)
            motions = []
            for j in range(0, nm):
                motions.append(obj({"pf": tok.nextInteger(0), "x": tok.nextInteger(0), "y": tok.nextInteger(0)}))
            characters.append(obj({"ac": ac, "nx": nx, "ny": ny, "nm": nm, "motions": motions}))
        return obj({"fc": fc, "fname": fname, "sf": sf, "scale": scale, "n": n, "characters": characters})
    def _write_310(d, pw, form):
        pw.writeInteger(d.fc)
        pw.writeString(d.fname or "")
        pw.writeInteger(d.sf)
        pw.writeInteger(d.scale)
        pw.writeInteger(len(d.characters))
        for c in d.characters:
            pw.writeInteger(c.ac)
            pw.writeInteger(c.nx)
            pw.writeInteger(c.ny)
            pw.writeInteger(len(c.motions))
            for m in c.motions:
                pw.writeInteger(m.pf)
                pw.writeInteger(m.x)
                pw.writeInteger(m.y)
    registerEntity(310, _parse_310, _write_310)

    def _parse_312(tok, form):
        return obj({"cbw": tok.nextReal(0), "cbh": tok.nextReal(0), "fc": tok.nextInteger(0), "sl": tok.nextReal(0), "a": tok.nextReal(0), "m": tok.nextInteger(0), "vh": tok.nextInteger(0), "xs": tok.nextReal(0), "ys": tok.nextReal(0), "zs": tok.nextReal(0)})
    def _write_312(d, pw, form):
        pw.writeReal(d.cbw)
        pw.writeReal(d.cbh)
        pw.writeInteger(d.fc)
        pw.writeReal(d.sl)
        pw.writeReal(d.a)
        pw.writeInteger(d.m)
        pw.writeInteger(d.vh)
        pw.writeReal(d.xs)
        pw.writeReal(d.ys)
        pw.writeReal(d.zs)
    registerEntity(312, _parse_312, _write_312)

    def _parse_314(tok, form):
        return obj({"red": tok.nextReal(0), "green": tok.nextReal(0), "blue": tok.nextReal(0), "name": tok.nextString("")})
    def _write_314(d, pw, form):
        pw.writeReal(d.red)
        pw.writeReal(d.green)
        pw.writeReal(d.blue)
        pw.writeString(d.name or "")
    registerEntity(314, _parse_314, _write_314)

    def _parse_316(tok, form):
        np = tok.nextInteger(0)
        units = []
        for i in range(0, np):
            units.append(obj({"typ": tok.nextString(""), "val": tok.nextString(""), "sf": tok.nextReal(0)}))
        return obj({"np": np, "units": units})
    def _write_316(d, pw, form):
        pw.writeInteger(len(d.units))
        for u in d.units:
            pw.writeString(u.typ or "")
            pw.writeString(u.val or "")
            pw.writeReal(u.sf)
    registerEntity(316, _parse_316, _write_316)

    def _parse_320(tok, form):
        depth = tok.nextInteger(0)
        name = tok.nextString("")
        na = tok.nextInteger(0)
        associated = []
        for i in range(0, na):
            associated.append(tok.nextPointer(0))
        tf = tok.nextInteger(0)
        prd = tok.nextString("")
        dptr = tok.nextPointer(0)
        nc = tok.nextInteger(0)
        connects = []
        for i in range(0, nc):
            connects.append(tok.nextPointer(0))
        return obj({"depth": depth, "name": name, "na": na, "associated": associated, "tf": tf, "prd": prd, "dptr": dptr, "nc": nc, "connects": connects})
    def _write_320(d, pw, form):
        pw.writeInteger(d.depth)
        pw.writeString(d.name or "")
        pw.writeInteger(len(d.associated))
        for p in d.associated:
            pw.writePointer(p)
        pw.writeInteger(d.tf)
        pw.writeString(d.prd or "")
        pw.writePointer(d.dptr or 0)
        pw.writeInteger(len(d.connects))
        for p in d.connects:
            pw.writePointer(p)
    registerEntity(320, _parse_320, _write_320)

    def _parse_322(tok, form):
        name = tok.nextString("")
        alt = tok.nextInteger(0)
        na = tok.nextInteger(0)
        attributes = []
        for i in range(0, na):
            at = tok.nextInteger(0)
            avdt = tok.nextInteger(0)
            avc = tok.nextInteger(0)
            values = []
            display_ptrs = []
            if form == 1 or form == 2:
                for j in range(0, avc):
                    v = readAttrValue(tok, avdt)
                    values.append(v)
                    if form == 2:
                        display_ptrs.append(tok.nextPointer(0))
            attributes.append(obj({"at": at, "avdt": avdt, "avc": avc, "values": values, "display_ptrs": display_ptrs}))
        return obj({"name": name, "alt": alt, "na": na, "attributes": attributes})
    def _write_322(d, pw, form):
        pw.writeString(d.name or "")
        pw.writeInteger(d.alt)
        pw.writeInteger(len(d.attributes))
        for a in d.attributes:
            pw.writeInteger(a.at)
            pw.writeInteger(a.avdt)
            pw.writeInteger(a.avc)
            if form == 1 or form == 2:
                for j in range(0, a.avc):
                    writeAttrValue(pw, a.avdt, a["values"][j])
                    if form == 2:
                        pw.writePointer(a.display_ptrs[j] or 0)
    registerEntity(322, _parse_322, _write_322)

    def _parse_402(tok, form):
        n = tok.nextInteger(0)
        entries = []
        for i in range(0, n):
            entries.append(tok.nextPointer(0))
        return obj({"n": n, "entries": entries})
    def _write_402(d, pw, form):
        pw.writeInteger(len(d.entries))
        for p in d.entries:
            pw.writePointer(p)
    registerEntity(402, _parse_402, _write_402)

    def _parse_404(tok, form):
        n = tok.nextInteger(0)
        views = []
        for i in range(0, n):
            view = tok.nextPointer(0)
            x_origin = tok.nextReal(0)
            y_origin = tok.nextReal(0)
            angle = tok.nextReal(0) if form == 1 else 0
            views.append(obj({"view": view, "x_origin": x_origin, "y_origin": y_origin, "angle": angle}))
        m = tok.nextInteger(0)
        annotations = []
        for i in range(0, m):
            annotations.append(tok.nextPointer(0))
        return obj({"n": n, "views": views, "m": m, "annotations": annotations})
    def _write_404(d, pw, form):
        pw.writeInteger(len(d.views))
        for v in d.views:
            pw.writePointer(v.view)
            pw.writeReal(v.x_origin)
            pw.writeReal(v.y_origin)
            if form == 1:
                pw.writeReal(v.angle or 0)
        pw.writeInteger(len(d.annotations))
        for p in d.annotations:
            pw.writePointer(p)
    registerEntity(404, _parse_404, _write_404)

    def _parse_406(tok, form):
        np = tok.nextInteger(0)
        values = []
        for i in range(0, np):
            values.append(readFieldValue(tok))
        return obj({"np": np, "values": values})
    def _write_406(d, pw, form):
        pw.writeInteger(len(d["values"]))
        for v in d["values"]:
            writeFieldValue(pw, v)
    registerEntity(406, _parse_406, _write_406)

    def _parse_408(tok, form):
        return obj({"de": tok.nextPointer(0), "translation": [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)], "scale": tok.nextReal(1)})
    def _write_408(d, pw, form):
        pw.writePointer(d.de)
        pw.writeReal(d.translation[0])
        pw.writeReal(d.translation[1])
        pw.writeReal(d.translation[2])
        pw.writeReal(d.scale if d.scale != None else 1)
    registerEntity(408, _parse_408, _write_408)

    def _parse_410(tok, form):
        view_number = tok.nextInteger(0)
        scale = tok.nextReal(1)
        d = obj({"form": form or 0, "view_number": view_number, "scale": scale, "clip_planes": [], "view_plane_normal": [0, 0, 1], "view_reference_point": [0, 0, 0], "center_of_projection": [0, 0, 0], "view_up_vector": [0, 1, 0], "view_plane_distance": 0, "umin": 0, "umax": 0, "vmin": 0, "vmax": 0, "depth_clipping": 0, "wmin": 0, "wmax": 0})
        if form == 1:
            d.view_plane_normal = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]
            d.view_reference_point = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]
            d.center_of_projection = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]
            d.view_up_vector = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]
            d.view_plane_distance = tok.nextReal(0)
            d.umin = tok.nextReal(0)
            d.umax = tok.nextReal(0)
            d.vmin = tok.nextReal(0)
            d.vmax = tok.nextReal(0)
            d.depth_clipping = tok.nextInteger(0)
            d.wmin = tok.nextReal(0)
            d.wmax = tok.nextReal(0)
        else:
            while not tok.atEnd():
                d.clip_planes.append(tok.nextPointer(0))
        return d
    def _write_410(d, pw, form):
        pw.writeInteger(d.view_number)
        pw.writeReal(d.scale)
        if form == 1:
            for v in d.view_plane_normal:
                pw.writeReal(v)
            for v in d.view_reference_point:
                pw.writeReal(v)
            for v in d.center_of_projection:
                pw.writeReal(v)
            for v in d.view_up_vector:
                pw.writeReal(v)
            pw.writeReal(d.view_plane_distance)
            pw.writeReal(d.umin)
            pw.writeReal(d.umax)
            pw.writeReal(d.vmin)
            pw.writeReal(d.vmax)
            pw.writeInteger(d.depth_clipping)
            pw.writeReal(d.wmin)
            pw.writeReal(d.wmax)
        else:
            for p in d.clip_planes:
                pw.writePointer(p)
    registerEntity(410, _parse_410, _write_410)

    def _parse_412(tok, form):
        de = tok.nextPointer(0)
        s = tok.nextReal(1)
        position = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]
        nc = tok.nextInteger(0)
        nr = tok.nextInteger(0)
        dx = tok.nextReal(0)
        dy = tok.nextReal(0)
        ax = tok.nextReal(0)
        lc = tok.nextInteger(0)
        ddf = tok.nextInteger(0)
        positions = []
        for i in range(0, lc):
            positions.append(tok.nextInteger(0))
        return obj({"de": de, "s": s, "position": position, "nc": nc, "nr": nr, "dx": dx, "dy": dy, "ax": ax, "lc": lc, "ddf": ddf, "positions": positions})
    def _write_412(d, pw, form):
        pw.writePointer(d.de)
        pw.writeReal(d.s if d.s != None else 1)
        pw.writeReal(d.position[0])
        pw.writeReal(d.position[1])
        pw.writeReal(d.position[2])
        pw.writeInteger(d.nc)
        pw.writeInteger(d.nr)
        pw.writeReal(d.dx)
        pw.writeReal(d.dy)
        pw.writeReal(d.ax)
        pw.writeInteger(len(d.positions))
        pw.writeInteger(d.ddf or 0)
        for p in d.positions:
            pw.writeInteger(p)
    registerEntity(412, _parse_412, _write_412)

    def _parse_414(tok, form):
        de = tok.nextPointer(0)
        ne = tok.nextInteger(0)
        center = [tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)]
        r = tok.nextReal(0)
        as_ = tok.nextReal(0)
        ad = tok.nextReal(0)
        lc = tok.nextInteger(0)
        ddf = tok.nextInteger(0)
        positions = []
        for i in range(0, lc):
            positions.append(tok.nextInteger(0))
        return obj({"de": de, "ne": ne, "center": center, "r": r, "as": as_, "ad": ad, "lc": lc, "ddf": ddf, "positions": positions})
    def _write_414(d, pw, form):
        pw.writePointer(d.de)
        pw.writeInteger(d.ne)
        pw.writeReal(d.center[0])
        pw.writeReal(d.center[1])
        pw.writeReal(d.center[2])
        pw.writeReal(d.r)
        pw.writeReal(d["as"])
        pw.writeReal(d.ad)
        pw.writeInteger(len(d.positions))
        pw.writeInteger(d.ddf or 0)
        for p in d.positions:
            pw.writeInteger(p)
    registerEntity(414, _parse_414, _write_414)

    def _parse_416(tok, form):
        if form == 1:
            return obj({"filename": tok.nextString(""), "entity_name": ""})
        if form == 3:
            return obj({"filename": "", "entity_name": tok.nextString("")})
        if form == 4:
            return obj({"filename": tok.nextString(""), "entity_name": tok.nextString("")})
        return obj({"filename": tok.nextString(""), "entity_name": tok.nextString("")})
    def _write_416(d, pw, form):
        if form == 1:
            pw.writeString(d.filename or "")
        elif form == 3:
            pw.writeString(d.entity_name or "")
        elif form == 4:
            pw.writeString(d.filename or "")
            pw.writeString(d.entity_name or "")
        else:
            pw.writeString(d.filename or "")
            pw.writeString(d.entity_name or "")
    registerEntity(416, _parse_416, _write_416)

    def _parse_418(tok, form):
        nc = tok.nextInteger(0)
        type = tok.nextInteger(0)
        de = tok.nextPointer(0)
        ptrs = []
        for i in range(0, nc):
            ptrs.append(tok.nextPointer(0))
        return obj({"nc": nc, "type": type, "de": de, "ptrs": ptrs})
    def _write_418(d, pw, form):
        pw.writeInteger(d.nc)
        pw.writeInteger(d.type)
        pw.writePointer(d.de)
        for p in d.ptrs:
            pw.writePointer(p)
    registerEntity(418, _parse_418, _write_418)

    def _parse_420(tok, form):
        de = tok.nextPointer(0)
        x = tok.nextReal(0)
        y = tok.nextReal(0)
        z = tok.nextReal(0)
        xs = tok.nextReal(1)
        ys = tok.nextReal(1)
        zs = tok.nextReal(1)
        tf = tok.nextInteger(0)
        prd = tok.nextString("")
        dptr = tok.nextPointer(0)
        nc = tok.nextInteger(0)
        cptrs = []
        for i in range(0, nc):
            cptrs.append(tok.nextPointer(0))
        return obj({"de": de, "x": x, "y": y, "z": z, "xs": xs, "ys": ys, "zs": zs, "tf": tf, "prd": prd, "dptr": dptr, "nc": nc, "cptrs": cptrs})
    def _write_420(d, pw, form):
        pw.writePointer(d.de)
        pw.writeReal(d.x)
        pw.writeReal(d.y)
        pw.writeReal(d.z)
        pw.writeReal(d.xs if d.xs != None else 1)
        pw.writeReal(d.ys if d.ys != None else d.xs or 1)
        pw.writeReal(d.zs if d.zs != None else d.xs or 1)
        pw.writeInteger(d.tf)
        pw.writeString(d.prd or "")
        pw.writePointer(d.dptr or 0)
        pw.writeInteger(len(d.cptrs))
        for p in d.cptrs:
            pw.writePointer(p)
    registerEntity(420, _parse_420, _write_420)

    def _parse_430(tok, form):
        return obj({"ptr": tok.nextPointer(0)})
    def _write_430(d, pw, form):
        pw.writePointer(d.ptr)
    registerEntity(430, _parse_430, _write_430)

    def _parse_502(tok, form):
        n = tok.nextInteger(0)
        vertices = []
        for i in range(0, n):
            vertices.append([tok.nextReal(0), tok.nextReal(0), tok.nextReal(0)])
        return obj({"n": n, "vertices": vertices})
    def _write_502(d, pw, form):
        pw.writeInteger(len(d.vertices))
        for v in d.vertices:
            pw.writeReal(v[0])
            pw.writeReal(v[1])
            pw.writeReal(v[2])
    registerEntity(502, _parse_502, _write_502)

    def _parse_504(tok, form):
        n = tok.nextInteger(0)
        edges = []
        for i in range(0, n):
            edges.append(obj({"curve": tok.nextPointer(0), "svp": tok.nextPointer(0), "sv": tok.nextInteger(0), "tvp": tok.nextPointer(0), "tv": tok.nextInteger(0)}))
        return obj({"n": n, "edges": edges})
    def _write_504(d, pw, form):
        pw.writeInteger(len(d.edges))
        for e in d.edges:
            pw.writePointer(e.curve)
            pw.writePointer(e.svp)
            pw.writeInteger(e.sv)
            pw.writePointer(e.tvp)
            pw.writeInteger(e.tv)
    registerEntity(504, _parse_504, _write_504)

    def _parse_508(tok, form):
        n = tok.nextInteger(0)
        edge_uses = []
        for i in range(0, n):
            type = tok.nextInteger(0)
            edge = tok.nextPointer(0)
            ndx = tok.nextInteger(0)
            orientation = tok.nextLogical(False)
            k = tok.nextInteger(0)
            param_curves = []
            for j in range(0, k):
                param_curves.append(obj({"isoparametric": tok.nextLogical(False), "curve": tok.nextPointer(0)}))
            edge_uses.append(obj({"type": type, "edge": edge, "ndx": ndx, "orientation": orientation, "k": k, "param_curves": param_curves}))
        return obj({"n": n, "edge_uses": edge_uses})
    def _write_508(d, pw, form):
        pw.writeInteger(len(d.edge_uses))
        for eu in d.edge_uses:
            pw.writeInteger(eu.type)
            pw.writePointer(eu.edge)
            pw.writeInteger(eu.ndx)
            pw.writeLogical(eu.orientation)
            pw.writeInteger(len(eu.param_curves))
            for pc in eu.param_curves:
                pw.writeLogical(pc.isoparametric)
                pw.writePointer(pc.curve)
    registerEntity(508, _parse_508, _write_508)

    def _parse_510(tok, form):
        surf = tok.nextPointer(0)
        n = tok.nextInteger(0)
        outer_loop_flag = tok.nextLogical(False)
        loops = []
        for i in range(0, n):
            loops.append(tok.nextPointer(0))
        return obj({"surf": surf, "n": n, "outer_loop_flag": outer_loop_flag, "loops": loops})
    def _write_510(d, pw, form):
        pw.writePointer(d.surf)
        pw.writeInteger(len(d.loops))
        pw.writeLogical(d.outer_loop_flag)
        for p in d.loops:
            pw.writePointer(p)
    registerEntity(510, _parse_510, _write_510)

    def _parse_514(tok, form):
        n = tok.nextInteger(0)
        faces = []
        for i in range(0, n):
            faces.append(obj({"face": tok.nextPointer(0), "orientation": tok.nextLogical(False)}))
        return obj({"n": n, "faces": faces})
    def _write_514(d, pw, form):
        pw.writeInteger(len(d.faces))
        for f in d.faces:
            pw.writePointer(f.face)
            pw.writeLogical(f.orientation)
    registerEntity(514, _parse_514, _write_514)

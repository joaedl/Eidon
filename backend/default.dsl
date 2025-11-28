part shaft {
  param dia = 20 mm tolerance g6
  param length = 80 mm

  feature base = cylinder(dia_param=dia, length_param=length)
  feature chamfer_end = chamfer(edge="end", size=1)

  chain length_chain {
    terms = [length]
  }
}


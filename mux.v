module mux(x1,x2,x3,x4,x5, out);
  input wire x1;
  input wire x2;
  input wire x3;
  input wire x4;
  input wire x5;
  output wire out;
  wire n2 = (~(x1&x2)) & (~(~x2 & x3));
  wire n3 = ((~x2 & x3) & (~(x4 & ~x5)));
  assign out = (~n2) & n3;
endmodule

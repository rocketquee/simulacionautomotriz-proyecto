function dxdt = quarter_car_model(t, x, p, zr_fun, u_fun)
% QUARTER_CAR_MODEL State-derivative function for 2-DOF vehicle suspension.
%
% Syntax:
%   dxdt = quarter_car_model(t, x, p, zr_fun, u_fun)
%
% Inputs:
%   t      - Current time (s)
%   x      - State vector [zs; zs_dot; zu; zu_dot]
%            zs:     Sprung mass displacement (m)
%            zs_dot: Sprung mass velocity (m/s)
%            zu:     Unsprung mass displacement (m)
%            zu_dot: Unsprung mass velocity (m/s)
%   p      - Parameter structure with fields:
%            p.ms: Sprung mass (kg)
%            p.mu: Unsprung mass (kg)
%            p.ks: Suspension spring stiffness (N/m)
%            p.cs: Suspension damping coefficient (N*s/m)
%            p.kt: Tire vertical stiffness (N/m)
%   zr_fun - Function handle zr = zr_fun(t) returning road displacement (m)
%   u_fun  - (Optional) Function handle u = u_fun(t, x) returning active/semi-active control force (N)
%
% Output:
%   dxdt   - State derivative column vector [zs_dot; zs_ddot; zu_dot; zu_ddot]

if nargin < 5 || isempty(u_fun)
    u = 0.0;
else
    u = u_fun(t, x);
end

zs     = x(1);
zs_dot = x(2);
zu     = x(3);
zu_dot = x(4);

% Road profile elevation at instant t
zr = zr_fun(t);

% Passive suspension spring and damping forces
f_spring = p.ks * (zs - zu);
f_damper = p.cs * (zs_dot - zu_dot);
f_susp_total = f_spring + f_damper + u;

% Tire contact vertical force
f_tire = p.kt * (zu - zr);

% Equations of motion:
%   ms * zs_ddot = -f_susp_total
%   mu * zu_ddot =  f_susp_total - f_tire
zs_ddot = -f_susp_total / p.ms;
zu_ddot = (f_susp_total - f_tire) / p.mu;

dxdt = [zs_dot; zs_ddot; zu_dot; zu_ddot];
end

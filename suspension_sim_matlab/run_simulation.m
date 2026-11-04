function results = run_simulation(params, excitation_type, excitation_opts, control_opts, t_span)
% RUN_SIMULATION Executes standalone quarter-car simulation using ODE45.
%
% Syntax:
%   results = run_simulation(params, excitation_type, excitation_opts, control_opts, t_span)
%
% Inputs:
%   params          - Struct with ms, mu, ks, cs, kt
%   excitation_type - 'bump', 'sine', or 'iso8608'
%   excitation_opts - Struct with excitation parameters
%   control_opts    - Struct:
%                     control_opts.active = true/false
%                     control_opts.sky_gain = c_sky (N*s/m)
%   t_span          - [t0, tf] (default [0, 5])
%
% Outputs:
%   results         - Struct with time series:
%                     t, zs, zs_dot, zs_ddot, zu, zu_dot, zu_ddot,
%                     zr, susp_deflection, tire_force, u_control,
%                     natural_freqs, params

if nargin < 1 || isempty(params)
    params = struct('ms', 300, 'mu', 40, 'ks', 15000, 'cs', 1500, 'kt', 200000);
end
if nargin < 2 || isempty(excitation_type)
    excitation_type = 'bump';
end
if nargin < 3 || isempty(excitation_opts)
    excitation_opts = struct('amplitude', 0.05, 'start_time', 0.5, 'duration', 0.2);
end
if nargin < 4 || isempty(control_opts)
    control_opts = struct('active', false, 'sky_gain', 1200);
end
if nargin < 5 || isempty(t_span)
    t_span = [0, 5.0];
end

% Create road function handle
zr_fun = excitation_profiles(excitation_type, excitation_opts);

% Create control law function handle
if control_opts.active
    c_sky = control_opts.sky_gain;
    u_fun = @(t, x) skyhook_control_law(x, c_sky);
else
    u_fun = @(t, x) 0.0;
end

% ODE45 Solver Options
ode_options = odeset('RelTol', 1e-6, 'AbsTol', 1e-8, 'MaxStep', 0.002);
x0 = [0.0; 0.0; 0.0; 0.0];

% Solve ODE
ode_handle = @(t, x) quarter_car_model(t, x, params, zr_fun, u_fun);
[t, x] = ode45(ode_handle, t_span, x0, ode_options);

% Extract and derive signals
N = length(t);
zs = x(:, 1);
zs_dot = x(:, 2);
zu = x(:, 3);
zu_dot = x(:, 4);

zr = arrayfun(zr_fun, t);
u_ctrl = zeros(N, 1);
for i = 1:N
    u_ctrl(i) = u_fun(t(i), x(i, :)');
end

susp_deflection = zs - zu;
susp_force = params.ks * susp_deflection + params.cs * (zs_dot - zu_dot) + u_ctrl;
tire_force = params.kt * (zu - zr);

zs_ddot = -susp_force / params.ms;
zu_ddot = (susp_force - tire_force) / params.mu;

% Analytical and exact natural frequencies
wn1_approx = sqrt(params.ks / params.ms) / (2 * pi);
wn2_approx = sqrt((params.ks + params.kt) / params.mu) / (2 * pi);

M_mat = [params.ms, 0; 0, params.mu];
K_mat = [params.ks, -params.ks; -params.ks, params.ks + params.kt];
eigvals = eig(K_mat, M_mat);
omegas = sort(sqrt(max(eigvals, 0)));
wn_exact = omegas / (2 * pi);

% Package results
results.t = t;
results.zs = zs;
results.zs_dot = zs_dot;
results.zs_ddot = zs_ddot;
results.zu = zu;
results.zu_dot = zu_dot;
results.zu_ddot = zu_ddot;
results.zr = zr;
results.susp_deflection = susp_deflection;
results.tire_force = tire_force;
results.u_control = u_ctrl;
results.params = params;
results.natural_freqs = struct(...
    'wn1_approx_hz', wn1_approx, ...
    'wn2_approx_hz', wn2_approx, ...
    'wn1_exact_hz', wn_exact(1), ...
    'wn2_exact_hz', wn_exact(2) ...
);

fprintf('=== Simulación Completada Exitosamente ===\n');
fprintf('Duración: %.2f s | Puntos de integración: %d\n', t(end), N);
fprintf('Frecuencia natural carrocería: %.2f Hz (desacoplada: %.2f Hz)\n', wn_exact(1), wn1_approx);
fprintf('Frecuencia natural rueda:       %.2f Hz (desacoplada: %.2f Hz)\n', wn_exact(2), wn2_approx);
end

function u = skyhook_control_law(x, c_sky)
zs_dot = x(2);
zu_dot = x(4);
rel_vel = zs_dot - zu_dot;

% Karnopp semi-active passivity condition
if (zs_dot * rel_vel) >= 0.0
    u = c_sky * zs_dot;
else
    u = 0.0;
end
end

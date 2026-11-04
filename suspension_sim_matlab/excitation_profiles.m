function zr_fun = excitation_profiles(type, options)
% EXCITATION_PROFILES Generates road profile function handles zr(t).
%
% Syntax:
%   zr_fun = excitation_profiles(type, options)
%
% Inputs:
%   type    - 'bump', 'sine', or 'iso8608'
%   options - Structure with relevant excitation configuration:
%             For 'bump':
%               options.amplitude (m, default 0.05)
%               options.start_time (s, default 0.5)
%               options.duration (s, default 0.2)
%             For 'sine':
%               options.amplitude (m, default 0.03)
%               options.frequency (Hz, default 1.5)
%               options.phase (rad, default 0.0)
%             For 'iso8608':
%               options.class ('A', 'B', 'C', 'D', 'E', default 'B')
%               options.speed_kmh (km/h, default 60)
%               options.seed (integer, default 42)
%
% Output:
%   zr_fun  - Function handle zr = zr_fun(t) returning road height in meters.

if nargin < 2
    options = struct();
end

switch lower(type)
    case 'bump'
        amp = get_field_default(options, 'amplitude', 0.05);
        t_start = get_field_default(options, 'start_time', 0.5);
        t_dur = max(get_field_default(options, 'duration', 0.2), 1e-4);
        
        zr_fun = @(t) step_bump_eval(t, amp, t_start, t_dur);

    case 'sine'
        amp = get_field_default(options, 'amplitude', 0.03);
        freq = get_field_default(options, 'frequency', 1.5);
        phase = get_field_default(options, 'phase', 0.0);
        
        zr_fun = @(t) amp * sin(2.0 * pi * freq * t + phase);

    case 'iso8608'
        iso_class = upper(get_field_default(options, 'class', 'B'));
        speed_kmh = max(get_field_default(options, 'speed_kmh', 60.0), 5.0);
        seed = get_field_default(options, 'seed', 42);
        
        % ISO 8608 PSD coefficient Gd(n0) at n0 = 0.1 cycles/m
        switch iso_class
            case 'A', gd_n0 = 16e-6;
            case 'B', gd_n0 = 64e-6;
            case 'C', gd_n0 = 256e-6;
            case 'D', gd_n0 = 1024e-6;
            case 'E', gd_n0 = 4096e-6;
            otherwise, gd_n0 = 64e-6;
        end
        
        speed_mps = speed_kmh / 3.6;
        n_harmonics = 200;
        n_min = 0.01;
        n_max = 3.0;
        n_vals = linspace(n_min, n_max, n_harmonics);
        dn = (n_max - n_min) / n_harmonics;
        n0 = 0.1;
        w = 2.0;
        
        psd_vals = gd_n0 * (n_vals / n0).^(-w);
        amplitudes = sqrt(2.0 * psd_vals * dn);
        omegas = 2.0 * pi * n_vals * speed_mps;
        
        % Deterministic pseudorandom phases
        rng(seed);
        phases = 2.0 * pi * rand(1, n_harmonics);
        
        zr_fun = @(t) iso_eval(t, amplitudes, omegas, phases);

    otherwise
        error('Unsupported excitation type: %s. Use "bump", "sine", or "iso8608".', type);
end
end

% Local helper functions
function val = get_field_default(s, field, default_val)
if isfield(s, field) && ~isempty(s.(field))
    val = s.(field);
else
    val = default_val;
end
end

function zr = step_bump_eval(t, amp, t_start, t_dur)
zr = zeros(size(t));
mask = (t >= t_start) & (t <= (t_start + t_dur));
if any(mask)
    phase = (t(mask) - t_start) / t_dur;
    zr(mask) = amp * sin(pi * phase);
end
end

function zr = iso_eval(t, amplitudes, omegas, phases)
zr = zeros(size(t));
for i = 1:numel(t)
    ti = t(i);
    zr(i) = sum(amplitudes .* cos(omegas * ti + phases));
end
end

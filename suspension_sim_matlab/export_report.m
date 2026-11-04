function export_report(results, base_filename)
% EXPORT_REPORT Exports simulation results to .mat, CSV, and summary text report.
%
% Syntax:
%   export_report(results, base_filename)
%
% Inputs:
%   results       - Struct returned by run_simulation
%   base_filename - Path prefix (without extension). Defaults to 'suspension_report'

if nargin < 2 || isempty(base_filename)
    base_filename = 'suspension_report';
end

% 1. Save binary MAT file
mat_file = [base_filename, '.mat'];
save(mat_file, 'results');
fprintf('Datos binarios guardados en: %s\n', mat_file);

% 2. Save portable CSV file
csv_file = [base_filename, '.csv'];
header = {'time', 'zs', 'zs_dot', 'zs_ddot', 'zu', 'zu_dot', 'zr', 'susp_deflection', 'tire_force', 'u_control'};
data_mat = [results.t, results.zs, results.zs_dot, results.zs_ddot, ...
            results.zu, results.zu_dot, results.zr, ...
            results.susp_deflection, results.tire_force, results.u_control];

T = array2table(data_mat, 'VariableNames', header);
writetable(T, csv_file);
fprintf('Series temporales exportadas en CSV: %s\n', csv_file);

% 3. Save Markdown executive summary report
md_file = [base_filename, '.md'];
fid = fopen(md_file, 'w');
if fid ~= -1
    p = results.params;
    nf = results.natural_freqs;
    
    rms_accel = sqrt(mean(results.zs_ddot.^2));
    peak_accel = max(abs(results.zs_ddot));
    peak_defl_mm = max(abs(results.susp_deflection)) * 1000;
    rms_defl_mm = sqrt(mean(results.susp_deflection.^2)) * 1000;
    peak_tire = max(abs(results.tire_force));
    rms_tire = sqrt(mean(results.tire_force.^2));
    
    fprintf(fid, '# Informe Tecnico de Simulacion MATLAB — Suspension Quarter-Car\n\n');
    fprintf(fid, '**Fecha:** %s  \n', datestr(now));
    fprintf(fid, '**Entorno:** MATLAB R2023a+ / App Designer  \n\n');
    
    fprintf(fid, '## 1. Parametros Fisicos\n');
    fprintf(fid, '- Masa suspendida (ms): %.1f kg\n', p.ms);
    fprintf(fid, '- Masa no suspendida (mu): %.1f kg\n', p.mu);
    fprintf(fid, '- Rigidez resorte (ks): %.1f N/m\n', p.ks);
    fprintf(fid, '- Amortiguador (cs): %.1f N*s/m\n', p.cs);
    fprintf(fid, '- Rigidez vertical neumatico (kt): %.1f N/m\n\n', p.kt);
    
    fprintf(fid, '## 2. Frecuencias Naturales\n');
    fprintf(fid, '| Modo | Desacoplada | Exacta (eig) |\n');
    fprintf(fid, '| :--- | :---: | :---: |\n');
    fprintf(fid, '| Carroceria (wn1) | %.2f Hz | %.2f Hz |\n', nf.wn1_approx_hz, nf.wn1_exact_hz);
    fprintf(fid, '| Rueda (wn2) | %.2f Hz | %.2f Hz |\n\n', nf.wn2_approx_hz, nf.wn2_exact_hz);
    
    fprintf(fid, '## 3. Metricas Dinamicas Clave\n');
    fprintf(fid, '- Aceleracion ms: Pico = %.3f m/s^2 | RMS = %.3f m/s^2\n', peak_accel, rms_accel);
    fprintf(fid, '- Deflexion suspension: Pico = %.2f mm | RMS = %.2f mm\n', peak_defl_mm, rms_defl_mm);
    fprintf(fid, '- Fuerza dinamica neumatico: Pico = %.1f N | RMS = %.1f N\n', peak_tire, rms_tire);
    
    fclose(fid);
    fprintf('Informe Markdown generado en: %s\n', md_file);
end

% 4. Export graphical plot figure
plot_results(results, [base_filename, '.png']);
end

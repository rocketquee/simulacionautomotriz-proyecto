function fig = plot_results(results, export_path)
% PLOT_RESULTS Displays the 4 engineering graphs from simulation results.
%
% Syntax:
%   fig = plot_results(results, export_path)
%
% Inputs:
%   results     - Struct returned by run_simulation
%   export_path - (Optional) File path to save PNG/PDF figure

if nargin < 1 || isempty(results)
    error('Must provide a valid results struct.');
end

t = results.t;
zs = results.zs;
zu = results.zu;
zr = results.zr;
zs_ddot = results.zs_ddot;
susp_deflection = results.susp_deflection;
tire_force = results.tire_force;

fig = figure('Name', 'Respuesta Dinamica de Suspension (Quarter-Car)', ...
             'Color', [0.12, 0.12, 0.13], ...
             'Position', [100, 100, 1100, 750]);

% Engineering dark theme styling
bg_color = [0.17, 0.18, 0.19];
text_color = [0.90, 0.91, 0.92];
grid_color = [0.35, 0.37, 0.40];

% Subplot 1: Vertical Displacements
ax1 = subplot(2, 2, 1);
plot(t, zr, '--', 'Color', [0.65, 0.65, 0.65], 'LineWidth', 1.5, 'DisplayName', 'zr (carretera)');
hold on;
plot(t, zu, 'Color', [1.0, 0.55, 0.25], 'LineWidth', 1.8, 'DisplayName', 'zu (rueda)');
plot(t, zs, 'Color', [0.3, 0.65, 1.0], 'LineWidth', 2.0, 'DisplayName', 'zs (carroceria)');
hold off;
title('Desplazamientos Verticales', 'Color', text_color, 'FontSize', 11, 'FontWeight', 'bold');
xlabel('Tiempo (s)', 'Color', text_color);
ylabel('Desplazamiento (m)', 'Color', text_color);
legend('Location', 'northeast', 'TextColor', text_color, 'Color', bg_color, 'EdgeColor', grid_color);
style_axes(ax1, bg_color, text_color, grid_color);

% Subplot 2: Body Vertical Acceleration
ax2 = subplot(2, 2, 2);
plot(t, zs_ddot, 'Color', [1.0, 0.35, 0.35], 'LineWidth', 1.8);
title('Aceleracion de Carroceria (zs\_ddot)', 'Color', text_color, 'FontSize', 11, 'FontWeight', 'bold');
xlabel('Tiempo (s)', 'Color', text_color);
ylabel('Aceleracion (m/s^2)', 'Color', text_color);
style_axes(ax2, bg_color, text_color, grid_color);

% Subplot 3: Working Suspension Deflection
ax3 = subplot(2, 2, 3);
plot(t, susp_deflection * 1000, 'Color', [0.2, 0.8, 0.6], 'LineWidth', 1.8);
title('Deflexion de Suspension (zs - zu)', 'Color', text_color, 'FontSize', 11, 'FontWeight', 'bold');
xlabel('Tiempo (s)', 'Color', text_color);
ylabel('Deflexion (mm)', 'Color', text_color);
style_axes(ax3, bg_color, text_color, grid_color);

% Subplot 4: Dynamic Tire Force
ax4 = subplot(2, 2, 4);
plot(t, tire_force, 'Color', [0.90, 0.66, 0.24], 'LineWidth', 1.8);
title('Fuerza Dinamica de Neumatico kt*(zu - zr)', 'Color', text_color, 'FontSize', 11, 'FontWeight', 'bold');
xlabel('Tiempo (s)', 'Color', text_color);
ylabel('Fuerza (N)', 'Color', text_color);
style_axes(ax4, bg_color, text_color, grid_color);

linkaxes([ax1, ax2, ax3, ax4], 'x');

if nargin >= 2 && ~isempty(export_path)
    exportgraphics(fig, export_path, 'Resolution', 300);
    fprintf('Grafica exportada exitosamente a: %s\n', export_path);
end
end

function style_axes(ax, bg_color, text_color, grid_color)
set(ax, 'Color', bg_color, ...
        'XColor', text_color, ...
        'YColor', text_color, ...
        'GridColor', grid_color, ...
        'GridAlpha', 0.4, ...
        'Box', 'on');
grid(ax, 'on');
end

classdef SuspensionApp < matlab.apps.AppBase

    % Properties that correspond to app components
    properties (Access = public)
        UIFigure                     matlab.ui.Figure
        GridLayout                   matlab.ui.container.GridLayout
        LeftPanel                    matlab.ui.container.Panel
        RightPanel                   matlab.ui.container.Panel
        
        % Sliders and Numerical Controls
        msSlider                     matlab.ui.control.Slider
        msEditField                  matlab.ui.control.NumericEditField
        muSlider                     matlab.ui.control.Slider
        muEditField                  matlab.ui.control.NumericEditField
        ksSlider                     matlab.ui.control.Slider
        ksEditField                  matlab.ui.control.NumericEditField
        csSlider                     matlab.ui.control.Slider
        csEditField                  matlab.ui.control.NumericEditField
        ktSlider                     matlab.ui.control.Slider
        ktEditField                  matlab.ui.control.NumericEditField
        
        % Road Excitation Controls
        RoadTypeDropDown             matlab.ui.control.DropDown
        RoadAmpEditField             matlab.ui.control.NumericEditField
        RoadFreqEditField            matlab.ui.control.NumericEditField
        ISOClassDropDown             matlab.ui.control.DropDown
        VehicleSpeedEditField        matlab.ui.control.NumericEditField
        
        % Control Strategy
        SkyhookCheckBox              matlab.ui.control.CheckBox
        SkyhookGainEditField         matlab.ui.control.NumericEditField
        
        % Simulation Flow Buttons
        SimDurationEditField         matlab.ui.control.NumericEditField
        SimSpeedDropDown             matlab.ui.control.DropDown
        PlayButton                   matlab.ui.control.Button
        PauseButton                  matlab.ui.control.Button
        ResetButton                  matlab.ui.control.Button
        DefaultButton                matlab.ui.control.Button
        ExportMatButton              matlab.ui.control.Button
        ExportReportButton           matlab.ui.control.Button
        SnapshotButton               matlab.ui.control.Button
        
        % Labels
        StatusLabel                  matlab.ui.control.Label
        NaturalFreqLabel             matlab.ui.control.Label
        
        % Axes
        UIAxes3D                     matlab.ui.control.UIAxes
        UIAxesDisp                   matlab.ui.control.UIAxes
        UIAxesAccel                  matlab.ui.control.UIAxes
        UIAxesDefl                   matlab.ui.control.UIAxes
        UIAxesForce                  matlab.ui.control.UIAxes
    end

    % Properties for simulation runtime and animation
    properties (Access = private)
        SimResults                   % Struct of ODE results
        AnimTimer                    timer
        CurrentFrameIndex = 1
        IsPlaying = false
        
        % 3D Graphic handles
        GroundPatch
        WheelPatch
        SpringPlot
        DamperBodyPatch
        DamperRodPatch
        ChassisPatch
    end

    methods (Access = private)

        function updateNaturalFrequenciesDisplay(app)
            ms = app.msEditField.Value;
            mu = app.muEditField.Value;
            ks = app.ksEditField.Value;
            kt = app.ktEditField.Value;

            wn1_approx = sqrt(ks / ms) / (2 * pi);
            wn2_approx = sqrt((ks + kt) / mu) / (2 * pi);

            M = [ms, 0; 0, mu];
            K = [ks, -ks; -ks, ks + kt];
            eigs = eig(K, M);
            wn_exact = sort(sqrt(max(eigs, 0))) / (2 * pi);

            app.NaturalFreqLabel.Text = sprintf(...
                'Frecuencias: Carroceria wn1=%.2f Hz (eig: %.2f Hz) | Rueda wn2=%.2f Hz (eig: %.2f Hz)', ...
                wn1_approx, wn_exact(1), wn2_approx, wn_exact(2));
        end

        function init3DScene(app)
            cla(app.UIAxes3D);
            hold(app.UIAxes3D, 'on');
            view(app.UIAxes3D, [35, 25]);
            axis(app.UIAxes3D, [-0.6, 0.6, -0.6, 0.6, -0.1, 1.3]);
            grid(app.UIAxes3D, 'on');
            app.UIAxes3D.Box = 'on';
            app.UIAxes3D.Color = [0.12, 0.12, 0.13];
            app.UIAxes3D.XColor = [0.7, 0.7, 0.7];
            app.UIAxes3D.YColor = [0.7, 0.7, 0.7];
            app.UIAxes3D.ZColor = [0.7, 0.7, 0.7];
            rotate3d(app.UIAxes3D, 'on');

            % 1. Ground Plane
            gx = [-0.5, 0.5, 0.5, -0.5];
            gy = [-0.4, -0.4, 0.4, 0.4];
            gz = [0, 0, 0, 0];
            app.GroundPatch = patch(app.UIAxes3D, 'XData', gx, 'YData', gy, 'ZData', gz, ...
                'FaceColor', [0.25, 0.27, 0.30], 'FaceAlpha', 0.8, 'EdgeColor', [0.4, 0.4, 0.4]);

            % 2. Wheel (cylinder patch at zu nominal = 0.35)
            [wx, wy, wz] = cylinder(0.28, 24);
            wz = wz * 0.16 - 0.08; % width 0.16 along Y
            % Rotate to align with axle
            app.WheelPatch = surf(app.UIAxes3D, wx, wz, wy + 0.35, ...
                'FaceColor', [0.15, 0.15, 0.17], 'EdgeColor', 'none');

            % 3. Helical Spring
            t_sp = linspace(0, 1, 150);
            sp_x = -0.10 + 0.05 * cos(2 * pi * 6 * t_sp);
            sp_y = 0.05 * sin(2 * pi * 6 * t_sp);
            sp_z = 0.35 + (0.90 - 0.35) * t_sp;
            app.SpringPlot = plot3(app.UIAxes3D, sp_x, sp_y, sp_z, ...
                'Color', [0.90, 0.66, 0.24], 'LineWidth', 2.5);

            % 4. Damper
            [dx, dy, dz] = cylinder(0.025, 16);
            app.DamperBodyPatch = surf(app.UIAxes3D, dx + 0.10, dy, dz * 0.25 + 0.35, ...
                'FaceColor', [0.12, 0.23, 0.37], 'EdgeColor', 'none');
            app.DamperRodPatch = surf(app.UIAxes3D, dx*0.5 + 0.10, dy*0.5, dz * 0.25 + 0.65, ...
                'FaceColor', [0.75, 0.78, 0.82], 'EdgeColor', 'none');

            % 5. Chassis Sprung Mass
            cx = [-0.35, 0.35, 0.35, -0.35, -0.35, 0.35, 0.35, -0.35];
            cy = [-0.25, -0.25, 0.25, 0.25, -0.25, -0.25, 0.25, 0.25];
            cz = [0.90, 0.90, 0.90, 0.90, 1.15, 1.15, 1.15, 1.15];
            faces = [1,2,3,4; 5,6,7,8; 1,2,6,5; 2,3,7,6; 3,4,8,7; 4,1,5,8];
            app.ChassisPatch = patch(app.UIAxes3D, 'Vertices', [cx', cy', cz'], 'Faces', faces, ...
                'FaceColor', [0.12, 0.23, 0.37], 'EdgeColor', [0.25, 0.40, 0.60]);

            hold(app.UIAxes3D, 'off');
        end

        function update3DPositions(app, zs, zu, zr)
            % Update ground
            set(app.GroundPatch, 'ZData', [zr, zr, zr, zr]);

            % Update wheel
            [wx, wy, wz] = cylinder(0.28, 24);
            wz = wz * 0.16 - 0.08;
            set(app.WheelPatch, 'XData', wx, 'YData', wz, 'ZData', wy + 0.35 + zu);

            % Update spring
            t_sp = linspace(0, 1, 150);
            sp_x = -0.10 + 0.05 * cos(2 * pi * 6 * t_sp);
            sp_y = 0.05 * sin(2 * pi * 6 * t_sp);
            sp_z = (0.35 + zu) + ((0.90 + zs) - (0.35 + zu)) * t_sp;
            set(app.SpringPlot, 'XData', sp_x, 'YData', sp_y, 'ZData', sp_z);

            % Update damper
            [dx, dy, dz] = cylinder(0.025, 16);
            set(app.DamperBodyPatch, 'XData', dx + 0.10, 'YData', dy, 'ZData', dz * 0.25 + 0.35 + zu);
            set(app.DamperRodPatch, 'XData', dx*0.5 + 0.10, 'YData', dy*0.5, 'ZData', dz * 0.25 + 0.65 + zs);

            % Update chassis
            cx = [-0.35, 0.35, 0.35, -0.35, -0.35, 0.35, 0.35, -0.35];
            cy = [-0.25, -0.25, 0.25, 0.25, -0.25, -0.25, 0.25, 0.25];
            cz = [0.90, 0.90, 0.90, 0.90, 1.15, 1.15, 1.15, 1.15] + zs;
            set(app.ChassisPatch, 'Vertices', [cx', cy', cz']);
        end

        function runFullODE(app)
            params.ms = app.msEditField.Value;
            params.mu = app.muEditField.Value;
            params.ks = app.ksEditField.Value;
            params.cs = app.csEditField.Value;
            params.kt = app.ktEditField.Value;

            road_type_str = app.RoadTypeDropDown.Value;
            switch road_type_str
                case 'Escalon (Bump)'
                    rtype = 'bump';
                    ropts.amplitude = app.RoadAmpEditField.Value;
                    ropts.start_time = 0.5;
                    ropts.duration = app.RoadFreqEditField.Value;
                case 'Senoidal'
                    rtype = 'sine';
                    ropts.amplitude = app.RoadAmpEditField.Value;
                    ropts.frequency = app.RoadFreqEditField.Value;
                case 'ISO 8608'
                    rtype = 'iso8608';
                    ropts.class = app.ISOClassDropDown.Value;
                    ropts.speed_kmh = app.VehicleSpeedEditField.Value;
            end

            copts.active = app.SkyhookCheckBox.Value;
            copts.sky_gain = app.SkyhookGainEditField.Value;
            dur = app.SimDurationEditField.Value;

            app.SimResults = run_simulation(params, rtype, ropts, copts, [0, dur]);
            app.CurrentFrameIndex = 1;
            app.updateNaturalFrequenciesDisplay();
        end

        function timerCallback(app, ~, ~)
            if isempty(app.SimResults) || ~app.IsPlaying
                return;
            end

            N = length(app.SimResults.t);
            idx = app.CurrentFrameIndex;

            if idx > N
                app.IsPlaying = false;
                stop(app.AnimTimer);
                app.PlayButton.Text = 'Iniciar / Play';
                app.StatusLabel.Text = 'Simulacion completada.';
                return;
            end

            t_sub = app.SimResults.t(1:idx);
            zs = app.SimResults.zs(idx);
            zu = app.SimResults.zu(idx);
            zr = app.SimResults.zr(idx);

            % Update 3D
            app.update3DPositions(zs, zu, zr);

            % Update 4 Plots
            plot(app.UIAxesDisp, t_sub, app.SimResults.zr(1:idx), '--', 'Color', [0.6, 0.6, 0.6]);
            hold(app.UIAxesDisp, 'on');
            plot(app.UIAxesDisp, t_sub, app.SimResults.zu(1:idx), 'Color', [1.0, 0.55, 0.25], 'LineWidth', 1.5);
            plot(app.UIAxesDisp, t_sub, app.SimResults.zs(1:idx), 'Color', [0.3, 0.65, 1.0], 'LineWidth', 1.8);
            hold(app.UIAxesDisp, 'off');
            legend(app.UIAxesDisp, {'zr', 'zu', 'zs'}, 'Location', 'northeast');

            plot(app.UIAxesAccel, t_sub, app.SimResults.zs_ddot(1:idx), 'Color', [1.0, 0.35, 0.35], 'LineWidth', 1.6);
            plot(app.UIAxesDefl, t_sub, app.SimResults.susp_deflection(1:idx)*1000, 'Color', [0.2, 0.8, 0.6], 'LineWidth', 1.6);
            plot(app.UIAxesForce, t_sub, app.SimResults.tire_force(1:idx), 'Color', [0.90, 0.66, 0.24], 'LineWidth', 1.6);

            app.StatusLabel.Text = sprintf('t=%.2f s | zs=%.1f mm | zu=%.1f mm | Acel=%.2f m/s^2', ...
                app.SimResults.t(idx), zs*1000, zu*1000, app.SimResults.zs_ddot(idx));

            % Step speed
            spd_val = str2double(strrep(app.SimSpeedDropDown.Value, 'x', ''));
            step_stride = max(1, round(spd_val * 4));
            app.CurrentFrameIndex = idx + step_stride;
        end

    end

    % Callbacks for UI interaction
    methods (Access = private)

        function PlayButtonPushed(app, ~)
            if isempty(app.SimResults)
                app.runFullODE();
            end
            app.IsPlaying = true;
            if strcmp(app.AnimTimer.Running, 'off')
                start(app.AnimTimer);
            end
            app.StatusLabel.Text = 'Simulacion en reproduccion...';
        end

        function PauseButtonPushed(app, ~)
            app.IsPlaying = false;
            app.StatusLabel.Text = 'Simulacion pausada.';
        end

        function ResetButtonPushed(app, ~)
            app.IsPlaying = false;
            stop(app.AnimTimer);
            app.CurrentFrameIndex = 1;
            cla(app.UIAxesDisp);
            cla(app.UIAxesAccel);
            cla(app.UIAxesDefl);
            cla(app.UIAxesForce);
            app.update3DPositions(0, 0, 0);
            app.StatusLabel.Text = 'Simulacion reiniciada.';
        end

        function DefaultButtonPushed(app, ~)
            app.msSlider.Value = 300; app.msEditField.Value = 300;
            app.muSlider.Value = 40;  app.muEditField.Value = 40;
            app.ksSlider.Value = 15000; app.ksEditField.Value = 15000;
            app.csSlider.Value = 1500;  app.csEditField.Value = 1500;
            app.ktSlider.Value = 200000; app.ktEditField.Value = 200000;
            app.RoadTypeDropDown.Value = 'Escalon (Bump)';
            app.SkyhookCheckBox.Value = false;
            app.updateNaturalFrequenciesDisplay();
            app.runFullODE();
        end

        function ExportMatButtonPushed(app, ~)
            if isempty(app.SimResults)
                app.runFullODE();
            end
            [file, path] = uiputfile('*.mat', 'Guardar archivo MAT', 'suspension_sim_results.mat');
            if ischar(file)
                results = app.SimResults;
                save(fullfile(path, file), 'results');
                uialert(app.UIFigure, 'Datos exportados correctamente.', 'Exito');
            end
        end

        function ExportReportButtonPushed(app, ~)
            if isempty(app.SimResults)
                app.runFullODE();
            end
            [file, path] = uiputfile('*.md', 'Guardar Reporte', 'informe_suspension.md');
            if ischar(file)
                [~, base_name] = fileparts(file);
                export_report(app.SimResults, fullfile(path, base_name));
                uialert(app.UIFigure, 'Informe y datos CSV exportados correctamente.', 'Exito');
            end
        end

        function SnapshotButtonPushed(app, ~)
            [file, path] = uiputfile('*.png', 'Guardar Captura', 'captura_suspension_3d.png');
            if ischar(file)
                exportgraphics(app.UIAxes3D, fullfile(path, file), 'Resolution', 300);
                uialert(app.UIFigure, 'Captura 3D guardada con exito.', 'Exito');
            end
        end

    end

end

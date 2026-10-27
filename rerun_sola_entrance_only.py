#!/usr/bin/env python3
"""Re-run Sola's analysis changing only source x' from -50 to -500."""

import math
import numpy as np
import ROOT


FILE_PATH = "/Users/s.x./Downloads/Muon_z.root"
R = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def gaussian_pdf(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (
        abs(sigma) * math.sqrt(2.0 * math.pi)
    )


def curve_fit_equivalent(x, y, initial):
    """Unweighted least-squares Gaussian fit matching scipy curve_fit's setup."""
    parameters = np.asarray(initial, dtype=float)
    damping = 1.0e-8
    for _ in range(200):
        mu, sigma, amplitude = parameters
        sigma = abs(sigma)
        pdf = gaussian_pdf(x, mu, sigma)
        model = amplitude * pdf
        residual = y - model
        jacobian = np.column_stack(
            (
                model * (x - mu) / sigma**2,
                model * (-1.0 / sigma + (x - mu) ** 2 / sigma**3),
                pdf,
            )
        )
        normal = jacobian.T @ jacobian + damping * np.eye(3)
        delta = np.linalg.solve(normal, jacobian.T @ residual)
        trial = parameters + delta
        if trial[1] <= 0:
            trial[1] = abs(trial[1])
        old_cost = float(residual @ residual)
        trial_model = trial[2] * gaussian_pdf(x, trial[0], trial[1])
        new_cost = float(np.sum((y - trial_model) ** 2))
        if new_cost <= old_cost:
            parameters = trial
            damping = max(damping / 3.0, 1.0e-14)
            if np.linalg.norm(delta) < 1.0e-11:
                break
        else:
            damping *= 10.0

    mu, sigma, amplitude = parameters
    pdf = gaussian_pdf(x, mu, sigma)
    model = amplitude * pdf
    jacobian = np.column_stack(
        (
            model * (x - mu) / sigma**2,
            model * (-1.0 / sigma + (x - mu) ** 2 / sigma**3),
            pdf,
        )
    )
    residual = y - model
    covariance = np.linalg.inv(jacobian.T @ jacobian)
    covariance *= float(residual @ residual) / (len(x) - 3)
    return parameters, covariance


def fit_central_98(values):
    low, high = np.percentile(values, [1.0, 99.0])
    trimmed = values[(values >= low) & (values <= high)]
    histogram, edges = np.histogram(trimmed, bins=100, density=True)
    centers = 0.5 * (edges[:-1] + edges[1:])
    parameters, covariance = curve_fit_equivalent(
        centers,
        histogram,
        [trimmed.mean(), trimmed.std(), 1.0],
    )
    errors = np.sqrt(np.diag(covariance))
    return parameters, errors


root_file = ROOT.TFile.Open(FILE_PATH)
exit_columns = [
    "Event_no",
    "exit_momentum_x",
    "exit_momentum_y",
    "exit_momentum_z",
]
exit_arrays = {
    key: np.asarray(value)
    for key, value in ROOT.RDataFrame(root_file.Get("Exit")).AsNumpy(
        exit_columns
    ).items()
}
exit_order = np.argsort(exit_arrays["Event_no"])
px = exit_arrays["exit_momentum_x"][exit_order]
py = exit_arrays["exit_momentum_y"][exit_order]
pz = exit_arrays["exit_momentum_z"][exit_order]
p = np.sqrt(px**2 + py**2 + pz**2)
px_rot, py_rot, pz_rot = R @ np.vstack((px, py, pz))
theta_momentum = np.degrees(np.arccos(np.clip(pz_rot / p, -1.0, 1.0)))
phi_momentum = np.degrees(np.arctan2(py_rot, px_rot))

gas_columns = ["Event_no", "x", "y", "z"]
gas_arrays = {
    key: np.asarray(value)
    for key, value in ROOT.RDataFrame(root_file.Get("Gas")).AsNumpy(
        gas_columns
    ).items()
}
# Equivalent to groupby(Event_no, sort=True).agg(list) followed by v[-1].
event = gas_arrays["Event_no"]
unique_event, reverse_first = np.unique(event[::-1], return_index=True)
last = len(event) - 1 - reverse_first
last_order = np.argsort(unique_event)
last = last[last_order]
x_last = gas_arrays["x"][last]
y_last = gas_arrays["y"][last]
z_last = gas_arrays["z"][last]
x_rot, y_rot, z_rot = R @ np.vstack((x_last, y_last, z_last))

(theta_mmt_fit, theta_mmt_err) = fit_central_98(theta_momentum)
(phi_mmt_fit, phi_mmt_err) = fit_central_98(phi_momentum)
sigma_theta_mmt = theta_mmt_fit[1]
sigma_phi_mmt = phi_mmt_fit[1]
sigma_theta_mmt_err = theta_mmt_err[1]
sigma_phi_mmt_err = phi_mmt_err[1]


def result(source_x):
    source = np.array([source_x, 0.0, 0.0])
    displacement = np.vstack((x_rot, y_rot, z_rot)).T - source
    distance = np.linalg.norm(displacement, axis=1)
    mask = distance > 0.0
    theta_hit = np.degrees(
        np.arccos(np.clip(displacement[mask, 2] / distance[mask], -1.0, 1.0))
    )
    phi_hit = np.degrees(
        np.arctan2(displacement[mask, 1], displacement[mask, 0])
    )
    theta_hit_fit, theta_hit_err = fit_central_98(theta_hit)
    phi_hit_fit, phi_hit_err = fit_central_98(phi_hit)

    theta_3d = math.hypot(sigma_theta_mmt, sigma_phi_mmt)
    theta_3d_err = math.sqrt(
        (sigma_theta_mmt * sigma_theta_mmt_err) ** 2
        + (sigma_phi_mmt * sigma_phi_mmt_err) ** 2
    ) / theta_3d
    psi_3d = math.hypot(theta_hit_fit[1], phi_hit_fit[1])
    psi_3d_err = math.sqrt(
        (theta_hit_fit[1] * theta_hit_err[1]) ** 2
        + (phi_hit_fit[1] * phi_hit_err[1]) ** 2
    ) / psi_3d

    theta_plane = theta_3d / math.sqrt(2.0)
    theta_plane_err = theta_3d_err / math.sqrt(2.0)
    psi_plane = psi_3d / math.sqrt(2.0)
    psi_plane_err = psi_3d_err / math.sqrt(2.0)
    ratio = theta_plane / psi_plane
    ratio_err = ratio * math.sqrt(
        (theta_plane_err / theta_plane) ** 2
        + (psi_plane_err / psi_plane) ** 2
    )
    return {
        "source_x": source_x,
        "theta_plane": theta_plane,
        "theta_plane_err": theta_plane_err,
        "psi_plane": psi_plane,
        "psi_plane_err": psi_plane_err,
        "ratio": ratio,
        "ratio_err": ratio_err,
        "sigma_theta_hit": theta_hit_fit[1],
        "sigma_phi_hit": phi_hit_fit[1],
    }


for source_x in (-50.0, -500.0):
    output = result(source_x)
    print(f"source = [{source_x:.0f}, 0, 0]")
    print(
        f"  theta_plane = {output['theta_plane']:.6f} +/- "
        f"{output['theta_plane_err']:.6f} deg"
    )
    print(
        f"  psi_plane   = {output['psi_plane']:.6f} +/- "
        f"{output['psi_plane_err']:.6f} deg"
    )
    print(
        f"  theta/psi   = {output['ratio']:.6f} +/- "
        f"{output['ratio_err']:.6f}"
    )
    print(
        f"  hit fit sigmas: theta={output['sigma_theta_hit']:.6f}, "
        f"phi={output['sigma_phi_hit']:.6f} deg"
    )

//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
/// \file B1/src/DetectorConstruction.cc
/// \brief Implementation of the B1::DetectorConstruction class
/// track every particle & interaction
/// sensitive dectector --> track it. automatically not detector
#include "DetectorConstruction.hh"

#include "G4Box.hh"
#include "G4Colour.hh"
#include "G4Cons.hh"
#include "G4LogicalVolume.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4PhysicalConstants.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4Trd.hh"
#include "G4VisAttributes.hh"
#include "MySensitiveDetector.hh"

namespace B1
{  //....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4VPhysicalVolume* DetectorConstruction::Construct()
{
    // 1. Get NIST material manager
    G4NistManager* nist = G4NistManager::Instance();

    // --- Define Custom Gas Mixture (He:CO2 70:30 at 10 atm) ---
    G4Element* elHe = nist->FindOrBuildElement("He");
    G4Element* elC = nist->FindOrBuildElement("C");
    G4Element* elO = nist->FindOrBuildElement("O");

    // Define CO2 molecule
    G4Material* CO2 = new G4Material("CO2", 1.842 * mg / cm3, 2, kStateGas);
    CO2->AddElement(elC, 1);
    CO2->AddElement(elO, 2);

    // Set pressure to 10 atm and temperature to 20 degC
    G4double pressure = 10.0 * atmosphere;
    G4double temperature = 293.15 * kelvin;

    G4double M_He = 4.0026 * g / mole;
    G4double M_CO2 = 44.0095 * g / mole;
    G4double M_avg = 0.7 * M_He + 0.3 * M_CO2;

    // rho = P * M / (R * T),  k_Boltzmann * Avogadro = R
    G4double gasDensity = pressure * M_avg
                          / (k_Boltzmann * Avogadro * temperature);

    G4Material* gasMix = new G4Material(
        "HeCO2_10atm", gasDensity, 2, kStateGas, temperature, pressure);
    gasMix->AddElement(elHe, 0.175);  // mass fraction of He
    gasMix->AddMaterial(CO2, 0.825);  // mass fraction of CO2
    // --- End of Material Definition ---

    G4bool checkOverlaps = true;

    // 2. World Volume
    // World size is set to 1.2m to contain the 1m cubic box
    G4double world_size = 1.2 * m;
    G4double vacDensity = universe_mean_density;
    G4double vacPressure = 1.e-19 * pascal;
    G4double vacTemperature = 0.1 * kelvin;
    G4Material* world_mat = new G4Material("Vacuum",
                                           1.,
                                           1.01 * g / mole,
                                           vacDensity,
                                           kStateGas,
                                           vacTemperature,
                                           vacPressure);

    /// logic -> material,properties
    auto solidWorld = new G4Box(
        "World", 0.5 * world_size, 0.5 * world_size, 0.5 * world_size);
    auto logicWorld = new G4LogicalVolume(solidWorld, world_mat, "World");
    auto physWorld = new G4PVPlacement(nullptr,
                                       G4ThreeVector(),
                                       logicWorld,
                                       "World",
                                       nullptr,
                                       false,
                                       0,
                                       checkOverlaps);

    // 3. Gas Box (1m x 1m x 1m cube)
    G4double box_size = 1.0 * m;
    auto solidBox
        = new G4Box("GasBox", 0.5 * box_size, 0.5 * box_size, 0.5 * box_size);

    // Fill the box with our custom gas mixture
    auto logicBox = new G4LogicalVolume(solidBox, gasMix, "GasBox");

    new G4PVPlacement(nullptr,  // no rotation
                      G4ThreeVector(),  // at (0,0,0)
                      logicBox,  // its logical volume
                      "GasBox",  // its name
                      logicWorld,  // its mother volume
                      false,  // no boolean operation
                      0,  // copy number
                      checkOverlaps);  // overlaps checking

    // 4. Set Scoring Volume
    // Set the entire gas box as the scoring volume to record energy deposits
    // (ionization)
    // --- Visual Attributes ---
    // Create a visual attribute: Cyan color, 0.3 transparency
    G4VisAttributes* boxVisAtt
        = new G4VisAttributes(G4Colour(0.0, 1.0, 1.0, 0.3));

    // Set to show as a solid (not just a wireframe)
    boxVisAtt->SetForceSolid(true);

    // Apply this attribute to your gas box
    logicBox->SetVisAttributes(boxVisAtt);

    return physWorld;
}

void DetectorConstruction::ConstructSDandField()
{
    MySensitiveDetector* SDBox = new MySensitiveDetector("SD");
    G4SDManager::GetSDMpointer()->AddNewDetector(SDBox);

    SetSensitiveDetector("GasBox", SDBox, true);
}
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
}  // namespace B1

//

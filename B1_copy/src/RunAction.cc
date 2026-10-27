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
/// \file B1/src/RunAction.cc
/// \brief Implementation of the B1::RunAction class

#include "RunAction.hh"

#include "DetectorConstruction.hh"
#include "G4AnalysisManager.hh"
#include "G4LogicalVolume.hh"
#include "G4ParticleDefinition.hh"
#include "G4ParticleGun.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"
#include "PrimaryGeneratorAction.hh"

namespace B1
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

RunAction::RunAction()
{
    G4RunManager::GetRunManager()->SetPrintProgress(1);
    auto analysisManager = G4AnalysisManager::Instance();

    analysisManager->SetVerboseLevel(1);
    analysisManager->SetNtupleMerging(true);
    analysisManager->SetDefaultFileType("root");
    analysisManager->SetFileName("msc_output");

    // creating ntuple
    G4int gasNtupleId = analysisManager->CreateNtuple(
        "Gas", "Energy Deposition and Position");
    analysisManager->CreateNtupleIColumn(gasNtupleId, "Event_no");
    analysisManager->CreateNtupleDColumn(gasNtupleId, "Edep");
    analysisManager->CreateNtupleDColumn(gasNtupleId, "x");
    analysisManager->CreateNtupleDColumn(gasNtupleId, "y");
    analysisManager->CreateNtupleDColumn(gasNtupleId, "z");
    analysisManager->FinishNtuple(gasNtupleId);

    G4int exitNtupleId
        = analysisManager->CreateNtuple("Exit", "Exit Momentum and Position");
    analysisManager->CreateNtupleIColumn(exitNtupleId, "Event_no");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "KE");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "exit_momentum_x");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "exit_momentum_y");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "exit_momentum_z");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "exit_pos_x");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "exit_pos_y");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "exit_pos_z");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "entry_KE");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "entry_momentum_x");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "entry_momentum_y");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "entry_momentum_z");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "entry_pos_x");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "entry_pos_y");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "entry_pos_z");
    analysisManager->CreateNtupleDColumn(exitNtupleId, "gas_track_length");
    analysisManager->CreateNtupleIColumn(exitNtupleId, "gas_step_count");
    analysisManager->CreateNtupleIColumn(exitNtupleId, "entered");
    analysisManager->FinishNtuple(exitNtupleId);

    // A compact step-level diagnostic is written only for the first ten
    // events.  It distinguishes geometric boundaries from the first recorded
    // non-zero energy-deposit hit.
    G4int stepNtupleId = analysisManager->CreateNtuple(
        "StepDebug", "Primary steps near and inside the gas");
    analysisManager->CreateNtupleIColumn(stepNtupleId, "Event_no");
    analysisManager->CreateNtupleIColumn(stepNtupleId, "Step_no");
    // Volume codes: 0 = World, 1 = GasBox, -1 = other.
    analysisManager->CreateNtupleIColumn(stepNtupleId, "pre_volume_code");
    analysisManager->CreateNtupleIColumn(stepNtupleId, "post_volume_code");
    analysisManager->CreateNtupleIColumn(stepNtupleId, "process_type");
    analysisManager->CreateNtupleIColumn(stepNtupleId, "process_subtype");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "step_length");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "pre_z");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "post_z");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "pre_px");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "pre_py");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "pre_pz");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "post_px");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "post_py");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "post_pz");
    analysisManager->CreateNtupleDColumn(stepNtupleId, "edep");
    analysisManager->FinishNtuple(stepNtupleId);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void RunAction::BeginOfRunAction(G4Run const*)
{
    auto analysisManager = G4AnalysisManager::Instance();
    // The macro can choose a non-destructive output path with
    // /analysis/setFileName <path>.  OpenFile() respects that setting.
    analysisManager->OpenFile();
    G4cout << "Using " << analysisManager->GetType() << G4endl;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void RunAction::EndOfRunAction(G4Run const* run)
{
    G4int nofEvents = run->GetNumberOfEvent();
    if (nofEvents == 0)
        return;

    auto analysisManager = G4AnalysisManager::Instance();

    analysisManager->Write();
    analysisManager->CloseFile();

    // Print
    //
    if (IsMaster())
    {
        G4cout
            << G4endl
            << "--------------------End of Global Run-----------------------";
    }
    else
    {
        G4cout
            << G4endl
            << "--------------------End of Local Run------------------------";
    }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace B1

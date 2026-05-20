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
    analysisManager->FinishNtuple(exitNtupleId);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void RunAction::BeginOfRunAction(G4Run const*)
{
    auto analysisManager = G4AnalysisManager::Instance();
    G4String fileName = "/Users/s.x./Data/TPC_Simulation/Muon.root";  /// name
                                                                      /// of
                                                                      /// the
                                                                      /// root
                                                                      /// file
    analysisManager->OpenFile(fileName);
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

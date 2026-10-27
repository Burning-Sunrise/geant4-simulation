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
/// \file B1/src/SteppingAction.cc
/// \brief Implementation of the B1::SteppingAction class

#include "SteppingAction.hh"

#include "DetectorConstruction.hh"
#include "EventAction.hh"
#include "G4AnalysisManager.hh"
#include "G4Event.hh"
#include "G4LogicalVolume.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
#include "G4VProcess.hh"
#include "G4SystemOfUnits.hh"

namespace B1
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

SteppingAction::SteppingAction(EventAction* eventAction)
    : fEventAction(eventAction)
{
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void SteppingAction::UserSteppingAction(G4Step const* step)
{
    auto prePoint = step->GetPreStepPoint();
    auto postPoint = step->GetPostStepPoint();
    auto preVol = prePoint->GetPhysicalVolume();
    auto postVol = postPoint->GetPhysicalVolume();
    auto track = step->GetTrack();

    if (!preVol || !postVol || track->GetTrackID() != 1)
        return;

    G4String preName = preVol->GetName();
    G4String postName = postVol->GetName();
    G4int pdgID = track->GetDefinition()->GetPDGEncoding();
    if (!(std::abs(pdgID) == 13 || pdgID == 2212))
        return;

    G4int eventID
        = G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();
    if (eventID < 10 && (preName == "GasBox" || postName == "GasBox"))
    {
        auto analysisManager = G4AnalysisManager::Instance();
        G4int preVolumeCode = preName == "World" ? 0 : 1;
        G4int postVolumeCode = postName == "World" ? 0 : 1;
        G4int processType = -1;
        G4int processSubtype = -1;
        if (postPoint->GetProcessDefinedStep())
        {
            processType = postPoint->GetProcessDefinedStep()->GetProcessType();
            processSubtype
                = postPoint->GetProcessDefinedStep()->GetProcessSubType();
        }
        G4ThreeVector preMom = prePoint->GetMomentum();
        G4ThreeVector postMom = postPoint->GetMomentum();
        analysisManager->FillNtupleIColumn(2, 0, eventID);
        analysisManager->FillNtupleIColumn(
            2, 1, track->GetCurrentStepNumber());
        analysisManager->FillNtupleIColumn(2, 2, preVolumeCode);
        analysisManager->FillNtupleIColumn(2, 3, postVolumeCode);
        analysisManager->FillNtupleIColumn(2, 4, processType);
        analysisManager->FillNtupleIColumn(2, 5, processSubtype);
        analysisManager->FillNtupleDColumn(2, 6, step->GetStepLength());
        analysisManager->FillNtupleDColumn(2, 7, prePoint->GetPosition().z());
        analysisManager->FillNtupleDColumn(2, 8, postPoint->GetPosition().z());
        analysisManager->FillNtupleDColumn(2, 9, preMom.x());
        analysisManager->FillNtupleDColumn(2, 10, preMom.y());
        analysisManager->FillNtupleDColumn(2, 11, preMom.z());
        analysisManager->FillNtupleDColumn(2, 12, postMom.x());
        analysisManager->FillNtupleDColumn(2, 13, postMom.y());
        analysisManager->FillNtupleDColumn(2, 14, postMom.z());
        analysisManager->FillNtupleDColumn(
            2, 15, step->GetTotalEnergyDeposit());
        analysisManager->AddNtupleRow(2);
    }

    if (preName == "GasBox")
        fEventAction->AddGasStep(step->GetStepLength());

    if (postPoint->GetStepStatus() == fGeomBoundary)
    {
        if (preName == "World" && postName == "GasBox")
        {
            fEventAction->SetEntryPos(postPoint->GetPosition());
            fEventAction->SetEntryMom(postPoint->GetMomentum());
            fEventAction->SetEntryKE(postPoint->GetKineticEnergy());
            fEventAction->SetEntered(true);
        }
        else if (preName == "GasBox" && postName == "World")
        {
            fEventAction->SetExitPos(postPoint->GetPosition());
            fEventAction->SetExitKE(postPoint->GetKineticEnergy());
            fEventAction->SetExitMom(postPoint->GetMomentum());
            fEventAction->SetExited(true);
            track->SetTrackStatus(fStopAndKill);
        }
    }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace B1

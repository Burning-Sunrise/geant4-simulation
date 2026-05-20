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
#include "G4Event.hh"
#include "G4LogicalVolume.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
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
    if (step->GetPostStepPoint()->GetStepStatus() == fGeomBoundary)
    {
        G4VPhysicalVolume* preVol
            = step->GetPreStepPoint()->GetPhysicalVolume();

        G4VPhysicalVolume* postVol
            = step->GetPostStepPoint()->GetPhysicalVolume();

        G4String vol1 = preVol->GetName();
        G4String vol2 = postVol->GetName();

        if (vol1 == "GasBox" && vol2 == "World")
        {
            G4Track* theTrack = step->GetTrack();
            G4int pdgID = theTrack->GetDefinition()->GetPDGEncoding();
            if (pdgID == 13 || pdgID == 2212)
            {
                G4ThreeVector pos = step->GetPostStepPoint()->GetPosition();
                fEventAction->SetExitPos(pos);

                G4double KE = theTrack->GetKineticEnergy();
                fEventAction->SetExitKE(KE);

                G4ThreeVector momentum = theTrack->GetMomentum();
                fEventAction->SetExitMom(momentum);

                theTrack->SetTrackStatus(fStopAndKill);
            }
        }
    }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace B1
